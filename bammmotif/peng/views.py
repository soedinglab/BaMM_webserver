import os
from os import path
from urllib.parse import urljoin

from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.conf import settings


from bammmotif.peng.io import (
    peng_bmscore_file_old,
    get_meme_result_file_path,
    get_plot_output_directory,
    file_path_peng,
    peng_meme_directory,
    get_peng_output_in_bamm_directory,
    get_peng_meme_output_in_bamm,
    media_memeplot_directory_html,
    media_bammplot_directory_html,
    media_memeplot_directory_from_peng_html,
    get_motif_init_file,
)

import bammmotif.bamm.tasks as bamm_tasks
from .utils import (
    upload_example_fasta_for_peng,
    copy_peng_to_bamm,
    load_meme_ids,
    zip_motifs,
    check_if_request_from_peng_directly,
    save_selected_motifs,
    upload_example_fasta,
    read_bmscore,
    merge_meme_and_bmscore,
)
from bammmotif.utils.misc import url_prefix
from bammmotif.forms import FindForm
from bammmotif.peng_utils import get_motif_ids
from bammmotif.utils.meme_reader import Meme, split_meme_file, get_n_motifs
from bammmotif.peng.settings import (
    MEME_PLOT_DIRECTORY, MEME_PLOT_INPUT, JOB_OUTPUT_DIRECTORY,
    NOT_ENOUGH_MOTIFS_SELECTED_FOR_REFINEMENT,
)

from ..utils import (
    get_user,
    set_job_name,
    get_job_output_folder,
    valid_uuid,
    get_result_folder,
    get_log_file,
    upload_example_fasta
)
from ..forms import (
    MetaJobNameForm,
)

from ..bamm.tasks import bamm_refinement_pipeline

from .tasks import peng_seeding_pipeline
from .forms import (
    PengToBammForm,
    get_valid_peng_form,
    PengExampleForm,
    PengForm,
)
from .job import (
    create_job,
    validate_input_data,
    init_job,
    create_bamm_job,
)
from .cmd_modules import PlotMeme
from .models import PengJob, JobInfo
from ..bamm.models import BaMMJob

from .settings import (
    get_meme_result_file_path,
    get_plot_output_directory,
    FILTERPWM_INPUT_FILE,
)


def peng_result_detail(request, pk):
    job_pk = pk
    result = get_object_or_404(PengJob, meta_job__pk=job_pk)
    meta_job = result.meta_job
    if result.meta_job.complete:
        meme_result_file_path = get_meme_result_file_path(job_pk)
        plot_output_directory = get_plot_output_directory(job_pk)
        bm_scores = read_bmscore(peng_bmscore_file_old(str(result.meta_job.pk), result.filename_prefix))
        if not path.exists(plot_output_directory):
            os.makedirs(plot_output_directory)
        meme_meta_info_list = Meme.fromfile(meme_result_file_path)
        meme_meta_info_list_old = Meme.fromfile(os.path.join(peng_meme_directory(str(pk)), FILTERPWM_INPUT_FILE))
        meme_meta_info_list_new = merge_meme_and_bmscore(meme_meta_info_list, meme_meta_info_list_old, bm_scores)

        return render(request, 'peng/peng_result_detail.html', {
            'result': result,
            'pk': result.meta_job.pk,
            'job_info': result.meta_job,
            'mode': result.meta_job.mode,
            'opath': media_memeplot_directory_html(result.meta_job.pk),
            'meme_meta_info': meme_meta_info_list_new,
        })
    else:
        log_file = get_log_file(job_pk)
        command = "tail -20 %r" % log_file
        output = os.popen(command).read()
        return render(request, 'results/result_status.html', {
            'output': output,
            'job_id': meta_job.pk,
            'job_name': meta_job.job_name,
            'status': meta_job.status,
        })


def run_peng_view(request, mode='normal'):
    if request.method == "POST":
        form, meta_job_form, valid, args = get_valid_peng_form(request.POST, request.FILES,
                                                               request.user, mode)

        if not valid:
            # TODO implement handling here
            pass

        peng_job = create_job(form, meta_job_form, request)
        job_pk = peng_job.meta_job.pk

        if mode == 'example':
            upload_example_fasta_for_peng(peng_job)
        ret, valid_input = validate_input_data(peng_job)

        with transaction.atomic():
            peng_job.meta_job.save()
            peng_job.save()

        peng_seeding_pipeline.delay(job_pk)
        return render(request, 'job/submitted.html', {'pk': job_pk, 'result_target': 'peng_results'})

    meta_job_form = MetaJobNameForm()
    if mode == 'example':
        form = PengExampleForm()
    else:
        form = PengForm()
    return render(request, 'job/peng_bamm_split_peng_input.html',
                  {
                    'form': form,
                    'meta_job_form': meta_job_form,
                    'mode': mode,
                  })


def find_peng_results(request, pk):
    if request.method == "POST":
        form = FindForm(request.POST)
        if form.is_valid():
            jobid = form.cleaned_data['job_ID']
            return redirect('peng_result_detail', pk=jobid)
        form = FindForm()
    return render(request, 'results/peng_results_main.html', {'form': form})





def peng_result_overview(request, pk):
    if request.user.is_authenticated:
        user_jobs = PengJob_deprecated.objects.filter(user=request.user.id)
        return render(request, 'results/peng_result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_peng_results')


def peng_load_bamm(request, pk):
    peng_job_pk = pk
    peng_job = get_object_or_404(PengJob, pk=pk)
    mode = "peng_to_bamm"
    inputfile = str(peng_job.fasta_file).rsplit('/', maxsplit=1)[1]

    if request.method == "POST":
        if check_if_request_from_peng_directly(request):
            at_least_one_motif_selected = save_selected_motifs(request.POST, pk)
            if not at_least_one_motif_selected:
                bm_scores = read_bmscore(peng_bmscore_file_old(str(peng_job.meta_job.pk), peng_job.filename_prefix))
                opath = os.path.join(get_result_folder(peng_job_pk), MEME_PLOT_DIRECTORY)
                meme_result_file_path = get_meme_result_file_path(peng_job_pk)
                meme_meta_info_list = Meme.fromfile(meme_result_file_path)
                meme_meta_info_list_old = Meme.fromfile(os.path.join(peng_meme_directory(str(pk)), FILTERPWM_INPUT_FILE))
                meme_meta_info_list_new = merge_meme_and_bmscore(meme_meta_info_list, meme_meta_info_list_old, bm_scores)
                return render(request, 'peng/peng_result_detail.html', {
                    'result': peng_job,
                    'pk': peng_job_pk,
                    'mode': peng_job.meta_job.mode,
                    'opath': opath,
                    'meme_meta_info': meme_meta_info_list_new,
                    'err_msg': NOT_ENOUGH_MOTIFS_SELECTED_FOR_REFINEMENT
                })
            form = PengToBammForm()
            return render(request, 'peng/peng_to_bamm.html', {
                'form': form,
                'mode': mode,
                'inputfile': inputfile,
                'job_name': peng_job.meta_job.job_name,
                'pk': peng_job_pk
            })
        form = PengToBammForm(request.POST, request.FILES)
        if form.is_valid():
            bamm_job = create_bamm_job('bamm', request, form, peng_job)
            bamm_job.MMcompare = True
            bamm_job_pk = bamm_job.meta_job.pk

            # Copy necessary files from last peng job.
            copy_peng_to_bamm(peng_job_pk, bamm_job_pk, request.POST)

            with transaction.atomic():
                bamm_job.meta_job.save()
                bamm_job.save()

            bamm_refinement_pipeline.delay(bamm_job_pk)

            return render(request, 'job/submitted.html', {'pk': bamm_job_pk, 'result_target': 'peng_to_bamm_results'})

        else:
            print(form.errors)

    form = PengToBammForm()
    return render(request, 'peng/peng_to_bamm.html', {
        'form': form,
        'mode': mode,
        'inputfile': inputfile,
        'job_name': peng_job.meta_job.job_name,
        'pk': pk
    })


def find_peng_to_bamm_results(request, pk):
    if request.method == "POST":
        form = FindForm(request.POST)
        if form.is_valid():
            jobid = form.cleaned_data['job_ID']
            if valid_uuid(jobid):
                job = Job.objects.get(pk=jobid).exists()
                if job.exists():
                    return redirect('peng_to_bamm_result_detail', pk=jobid)
            form = FindForm()
            return render(request, 'results/peng_to_bamm_results_main.html', {'form': form, 'warning': True})
    else:
        form = FindForm()
    return render(request, 'results/peng_to_bamm_result_main.html', {'form': form, 'warning': False})

def peng_to_bamm_result_overview(request, pk):
    if request.user.is_authenticated:
        user_jobs = Job.objects.filter(user=request.user.id)
        return render(request, 'results/peng_to_bamm_result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_peng_to_bamm_results')


def peng_to_bamm_result_detail(request, pk):
    result = get_object_or_404(BaMMJob, meta_job__pk=pk)
    meta_job = result.meta_job

    relative_result_folder = get_result_folder(pk)
    job_output_dir = get_job_output_folder(pk)
    peng_path = path.join(job_output_dir, "pengoutput")
    meme_plots = path.join(job_output_dir, "pengoutput", "meme_plots")
    meme_motifs = load_meme_ids(peng_path)
    #meme_meta_info_list = Meme.fromfile(os.path.join(peng_path, "out.meme"))
    meme_meta_info_list = Meme.fromfile(get_motif_init_file(str(meta_job.job_id)))

    motif_db = result.motif_db
    db_dir = motif_db.relative_db_model_dir

    if meta_job.complete:
        num_logos = range(1, (min(2, result.model_order)+1))
        return render(request, 'bamm/bamm_result_detail.html', {
            'result': result, 'opath': get_result_folder(pk),
            'mode': meta_job.mode,
            'Output_filename': result.filename_prefix,
            'num_logos': num_logos,
            'db_dir': db_dir,
            'meme_logo_path': path.relpath(meme_plots, relative_result_folder),
            'meme_motifs': meme_motifs,
            'meme_meta_info': meme_meta_info_list,
        })
    else:
        log_file = get_log_file(pk)
        command = "tail -20 %r" % log_file
        output = os.popen(command).read()
        return render(request, 'results/result_status.html', {
                'output': output,
                'job_id': meta_job.pk,
                'job_name': meta_job.job_name,
                'status': meta_job.status
        })

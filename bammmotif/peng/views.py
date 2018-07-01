import os
from os import path
import itertools

from django.shortcuts import render, get_object_or_404
from django.db import transaction
from django.conf import settings

from ..views import redirect_if_not_ready


from bammmotif.peng.io import (
    peng_bmscore_file_old,
    get_meme_result_file_path,
    get_plot_output_directory,
    peng_meme_directory,
    media_memeplot_directory_html,
    get_motif_init_file,
)

from .utils import (
    upload_example_fasta_for_peng,
    copy_peng_to_bamm,
    load_meme_ids,
    check_if_request_from_peng_directly,
    save_selected_motifs,
    upload_example_fasta,
    read_bmscore,
    merge_meme_and_bmscore,
    get_selected_motifs,
)
from ..utils import (
    register_job_session,
    check_fasta_input,
)


from bammmotif.forms import FindForm
from bammmotif.utils.meme_reader import Meme, split_meme_file, get_n_motifs
from bammmotif.peng.settings import (
    MEME_PLOT_DIRECTORY,
    MEME_PLOT_INPUT,
    JOB_OUTPUT_DIRECTORY,
    NOT_ENOUGH_MOTIFS_SELECTED_FOR_REFINEMENT,
    MOTIF_SELECT_IDENTIFIER,
)

from ..utils import (
    get_user,
    get_job_output_folder,
    valid_uuid,
    get_result_folder,
    get_log_file,
    upload_example_fasta
)
from ..forms import (
    MetaJobNameForm,
    GenomeBrowserForm,
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


def peng_results(request, pk):
    redirect_obj = redirect_if_not_ready(pk)
    if redirect_obj is not None:
        return redirect_obj

    job_pk = pk
    result = get_object_or_404(PengJob, meta_job__pk=job_pk)

    meme_result_file_path = get_meme_result_file_path(job_pk)
    plot_output_directory = get_plot_output_directory(job_pk)

    bm_scores = read_bmscore(peng_bmscore_file_old(str(result.meta_job.pk), result.filename_prefix))
    if not path.exists(plot_output_directory):
        os.makedirs(plot_output_directory)
    filtered_meme = Meme.fromfile(meme_result_file_path)
    unfiltered_meme = Meme.fromfile(os.path.join(peng_meme_directory(str(pk)), FILTERPWM_INPUT_FILE))
    final_motifs = merge_meme_and_bmscore(filtered_meme, unfiltered_meme, bm_scores)

    return render(request, 'peng/peng_result.html', {
        'result': result,
        'pk': result.meta_job.pk,
        'job_info': result.meta_job,
        'mode': result.meta_job.mode,
        'opath': media_memeplot_directory_html(result.meta_job.pk),
        'meme_meta_info': final_motifs,
        'max_seeds': settings.MAX_SEEDS_FOR_REFINEMENT,
    })


def run_peng_view(request, mode='normal'):

    if request.method == "POST":
        form, meta_job_form, valid, args = get_valid_peng_form(request.POST, request.FILES,
                                                               request.user, mode)
        is_valid = valid
        if is_valid:
            peng_job = create_job(form, meta_job_form, request)
            job_pk = peng_job.meta_job.pk

            if mode == 'example':
                upload_example_fasta_for_peng(peng_job)
            else:
                is_valid = check_fasta_input(peng_job, form, request.FILES)

            if peng_job.bg_sequences:
                is_bg_valid = check_fasta_input(peng_job, form, request.FILES, bg_seqs=True)
                is_valid = is_valid and is_bg_valid

            if is_valid:
                with transaction.atomic():
                    peng_job.meta_job.save()
                    register_job_session(request, peng_job.meta_job)
                    peng_job.save()

                peng_seeding_pipeline.delay(job_pk)
                return render(request, 'job/submitted.html', {
                    'pk': job_pk,
                    'result_target': 'peng_results'
                })
    else:
        meta_job_form = MetaJobNameForm()
        if mode == 'example':
            form = PengExampleForm()
        else:
            form = PengForm()
        is_valid = True

    return render(request, 'peng/peng_seeding.html', {
        'job_form': form,
        'metajob_form': meta_job_form,
        'mode': mode,
        'all_form_fields': itertools.chain(meta_job_form, form),
        'max_file_size': settings.MAX_UPLOAD_FILE_SIZE,
        'validation_errors': not is_valid,
    })


def run_refine(request, pk):
    peng_job_pk = pk
    peng_job = get_object_or_404(PengJob, pk=pk)
    mode = "peng_to_bamm"
    inputfile = str(peng_job.fasta_file).rsplit('/', maxsplit=1)[1]

    if request.method == "POST":
        max_seeds = settings.MAX_SEEDS_FOR_REFINEMENT
        if check_if_request_from_peng_directly(request):
            selected_motif_keys = [x for x in request.POST.keys() if x.endswith(MOTIF_SELECT_IDENTIFIER)]
            if len(selected_motif_keys) == 0 or len(selected_motif_keys) > max_seeds:
                
                if len(selected_motif_keys) == 0:
                    err_msg = NOT_ENOUGH_MOTIFS_SELECTED_FOR_REFINEMENT
                else:
                    err_msg = 'Please select only %s seeds.' % max_seeds

                bm_scores = read_bmscore(peng_bmscore_file_old(str(peng_job.meta_job.pk), peng_job.filename_prefix))
                opath = os.path.join(get_result_folder(peng_job_pk), MEME_PLOT_DIRECTORY)
                meme_result_file_path = get_meme_result_file_path(peng_job_pk)
                meme_meta_info_list = Meme.fromfile(meme_result_file_path)
                meme_meta_info_list_old = Meme.fromfile(os.path.join(peng_meme_directory(str(pk)), FILTERPWM_INPUT_FILE))
                meme_meta_info_list_new = merge_meme_and_bmscore(meme_meta_info_list, meme_meta_info_list_old, bm_scores)
                return render(request, 'peng/peng_result.html', {
                    'result': peng_job,
                    'job_info': peng_job.meta_job,
                    'pk': peng_job_pk,
                    'mode': peng_job.meta_job.mode,
                    'opath': opath,
                    'meme_meta_info': meme_meta_info_list_new,
                    'err_msg': err_msg,
                    'max_seeds': max_seeds,
                })
            form = PengToBammForm()
            metajob_form = MetaJobNameForm()
            return render(request, 'bamm/refine_input.html', {
                'validation_errors': False,
                'job_form': form,
                'metajob_form': metajob_form,
                'all_form_fields': itertools.chain(metajob_form, form),
                'mode': mode,
                'inputfile': inputfile,
                'job_name': peng_job.meta_job.job_name,
                'pk': peng_job_pk,
                'selected_motif_keys': selected_motif_keys,
            })
        form = PengToBammForm(request.POST, request.FILES)

        # the user gets here when he/she reloads the page or does other dirty tricks.
        # in this case the information about the selected motifs gets lost and the
        # user has to start over again
        if len(get_selected_motifs(request.POST)) == 0:
            bm_scores = read_bmscore(peng_bmscore_file_old(
                str(peng_job.meta_job.pk), peng_job.filename_prefix))
            opath = os.path.join(get_result_folder(peng_job_pk), MEME_PLOT_DIRECTORY)
            meme_result_file_path = get_meme_result_file_path(peng_job_pk)
            meme_meta_info_list = Meme.fromfile(meme_result_file_path)
            meme_meta_info_list_old = Meme.fromfile(
                path.join(peng_meme_directory(str(pk)), FILTERPWM_INPUT_FILE))
            meme_meta_info_list_new = merge_meme_and_bmscore(
                meme_meta_info_list, meme_meta_info_list_old, bm_scores)

            return render(request, 'peng/peng_result.html', {
                'result': peng_job,
                'pk': peng_job_pk,
                'mode': peng_job.meta_job.mode,
                'opath': opath,
                'meme_meta_info': meme_meta_info_list_new,
                'job_info': peng_job.meta_job,
            })

        if form.is_valid():
            bamm_job = create_bamm_job('refine', request, form, peng_job)
            bamm_job_pk = bamm_job.meta_job.pk

            # Copy necessary files from last peng job.
            selected_motifs = get_selected_motifs(request.POST)
            copy_peng_to_bamm(peng_job_pk, bamm_job_pk, selected_motifs)
            save_selected_motifs(selected_motifs, peng_job.meta_job.pk, bamm_job_pk)
            bamm_job.num_motifs = len(selected_motifs)
            bamm_job.Background_Sequences = peng_job.bg_sequences

            with transaction.atomic():
                bamm_job.meta_job.save()
                bamm_job.save()

            bamm_refinement_pipeline.delay(bamm_job_pk)

            return render(request, 'job/submitted.html', {
                'pk': bamm_job_pk,
                'result_target': 'peng_to_bamm_results'
            })

        else:
            return render(request, 'bamm/refine_input', {
                'validation_errors': True,
                'job_form': form,
                'metajob_form': metajob_form,
                'all_form_fields': itertools.chain(metajob_form, form),
                'mode': mode,
                'inputfile': inputfile,
                'job_name': peng_job.meta_job.job_name,
                'pk': peng_job_pk,
                'selected_motif_keys': selected_motif_keys,
            })

    form = PengToBammForm()
    metajob_form = MetaJobNameForm()
    return render(request, 'bamm/refine_input.html', {
        'validation_errors': False,
        'job_form': form,
        'metajob_form': metajob_form,
        'all_form_fields': itertools.chain(metajob_form, form),
        'mode': mode,
        'inputfile': inputfile,
        'job_name': peng_job.meta_job.job_name,
        'pk': pk
    })


def peng_to_bamm_result_detail(request, pk):

    redirect_obj = redirect_if_not_ready(pk)
    if redirect_obj is not None:
        return redirect_obj

    result = get_object_or_404(BaMMJob, meta_job__pk=pk)
    meta_job = result.meta_job

    relative_result_folder = get_result_folder(pk)
    job_output_dir = get_job_output_folder(pk)
    peng_path = path.join(job_output_dir, "pengoutput")
    meme_plots = path.join(job_output_dir, "pengoutput", "meme_plots")
    meme_motifs = load_meme_ids(peng_path)
    meme_meta_info_list = Meme.fromfile(get_motif_init_file(str(meta_job.job_id)))

    motif_db = result.motif_db
    db_dir = motif_db.relative_db_model_dir

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
        'genome_browser_form': GenomeBrowserForm(),
    })

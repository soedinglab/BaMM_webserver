import os
import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings

from bammmotif.peng_to_bamm_form import PengToBammForm
from bammmotif.peng.form import get_valid_peng_form, PengExampleForm, PengForm
from bammmotif.peng.job import create_job, validate_input_data
from bammmotif.peng.tasks import run_peng, plot_meme, peng_chain
from bammmotif.peng.utils import upload_example_fasta_for_peng, copy_peng_to_bamm, load_meme_ids, zip_motifs, \
    check_if_request_from_peng_directly, save_selected_motifs
from bammmotif.models import Job, PengJob, DbParameter
from bammmotif.forms import FindForm
from bammmotif.peng.job import file_path_peng
from bammmotif.peng_utils import get_motif_ids
from bammmotif.command_line import PlotMeme
from bammmotif.utils.meme_reader import Meme, split_meme_file, get_n_motifs
from bammmotif.utils import (
    get_log_file,
    get_user, set_job_name, valid_uuid,
    get_result_folder,
)
import bammmotif.tasks as tasks
from bammmotif.peng.settings import MEME_PLOT_DIRECTORY

def peng_result_detail(request, pk):
    result = get_object_or_404(PengJob, pk=pk)
    meme_result_file_path = file_path_peng(result.job_ID, result.meme_output)
    if result.complete:
        print("status is successfull")
        plot_output_directory = os.path.join(meme_result_file_path.rsplit('/', maxsplit=1)[0], MEME_PLOT_DIRECTORY)
        opath = os.path.join(get_result_folder(result.job_ID), MEME_PLOT_DIRECTORY).split('/', maxsplit=1)[1]
        if not os.path.exists(plot_output_directory):
            os.makedirs(plot_output_directory)
        motif_ids = get_motif_ids(meme_result_file_path)
        meme_plotter = PlotMeme()
        meme_plotter.output_file_format = PlotMeme.defaults['output_file_format']
        meme_meta_info_list = Meme.fromfile(meme_result_file_path)
        return render(request, 'results/peng_result_detail.html',
                      {'result': result,
                         'mode': result.mode,
                         'motif_ids': motif_ids,
                         'opath': opath,
                         'meme_meta_info': meme_meta_info_list,
                         })
    else:
        print('status not ready yet')
        log_file = get_log_file(pk)
        command = "tail -20 %r" % log_file
        output = os.popen(command).read()
        return render(request, 'results/result_status.html',
                      {'result': result, 'output': output})


def run_peng_view(request, mode='normal'):
    print("ENTERING Data PREDICT VIEW data_peng_changed: ", request.method, mode)
    if request.method == "POST":
        print("run_peng_view: Request IS POST")
        # Reformat get valid form.
        form, valid, args = get_valid_peng_form(request.POST, request.FILES, request.user, mode)
        if not valid:
            print("FORM IS NOT VALID!!!!!")
            pass
            # return render(request, 'job/de_novo_search.html', args)
        peng_job = create_job(form, request)
        ret, valid_input = validate_input_data(peng_job)
        if not valid_input:
            Job.objects.filter(job_ID=peng_job.pk).delete()
            # return render(request, 'job/de_novo_search.html', {'form': PengForm(), 'type': "Fasta", 'message': ret})
        if mode == 'example':
            upload_example_fasta_for_peng(peng_job.job_ID)
        peng_chain.delay(peng_job.job_ID)
        return render(request, 'job/peng_bamm_split_submitted.html', {'pk': peng_job.job_ID})
    if mode == 'example':
        form = PengExampleForm()
    else:
        form = PengForm()
    print("Request IS NOT POST -> make form and redirect")
    return render(request, 'job/peng_bamm_split_peng_input.html',
                  {'form': form, 'mode': mode})

def find_peng_results(request, pk):
    if request.method == "POST":
        form = FindForm(request.POST)
        if form.is_valid():
            jobid = form.cleaned_data['job_ID']
            return redirect('peng_result_detail', pk=jobid)
        form = FindForm()
    return render(request, 'results/peng_results_main.html', {'form': form})

def peng_result_overview(request, pk):
    if request.user.is_authenticated():
        user_jobs = PengJob.objects.filter(user=request.user.id)
        return render(request, 'results/peng_result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_peng_results')

def peng_load_bamm(request, pk):
    mode = "peng_to_bamm"
    peng_job = get_object_or_404(PengJob, pk=pk)
    inputfile = str(peng_job.fasta_file).rsplit('/', maxsplit=1)[1]
    print("peng_load_bamm")
    if request.method == "POST":
        # TODO: Maybe do that differently.
        if check_if_request_from_peng_directly(request):
            save_selected_motifs(request.POST, pk)
            form = PengToBammForm()
            return render(request, 'job/peng_bamm_split_peng_to_bamm.html',
                          {'form': form, 'mode': mode, 'inputfile': inputfile, 'job_name': peng_job.job_name, 'pk': pk})
        form = PengToBammForm(request.POST, request.FILES)
        if form.is_valid():
            # read in data and parameter
            job = form.save(commit=False)
            job.created_at = datetime.datetime.now()
            job.user = get_user(request)
            job.Input_Sequences = peng_job.fasta_file
            job.num_init_motifs = get_n_motifs(pk)
            job_pk = str(job.job_ID)
            # print(dir(peng_job.fasta_file))
            job.Motif_InitFile.name = os.path.join(settings.MEDIA_ROOT, str(job_pk), 'pengoutput', 'out.meme')
            job.save()
            job.Motif_Initialization = "Custom File"
            job.Motif_Init_File_Format = "PWM"
            #TODO: Find a nicer way to write that.
            if job.job_name is None:
                set_job_name(job_pk)
            # Copy necessary files from last peng job.
            copy_peng_to_bamm(pk, job_pk, request.POST)
            print("Job Motif Initialisation")
            print(job.Motif_Initialization)
            print("Job ID", job.job_ID)
            if job.Motif_Initialization == 'PEnGmotif':
                tasks.run_peng.delay(job.job_ID)
            else:
                tasks.run_bamm.delay(job.job_ID)
            return render(request, 'job/peng_to_bamm_submitted.html', {'pk': job_pk})
        else:
            print("peng_load_bamm: Form is invalid!")
    form = PengToBammForm()
    return render(request, 'job/peng_bamm_split_peng_to_bamm.html',
                  {'form': form, 'mode': mode, 'inputfile': inputfile, 'job_name': peng_job.job_name, 'pk': pk})


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
    if request.user.is_authenticated():
        user_jobs = Job.objects.filter(user=request.user.id)
        return render(request, 'results/peng_to_bamm_result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_peng_to_bamm_results')

def peng_to_bamm_result_detail(request, pk):
    result = get_object_or_404(Job, pk=pk)
    opath = get_result_folder(pk)
    Output_filename = result.Output_filename()
    # meme_logo_path = peng_meme_directory(pk)
    peng_path = os.path.join(settings.MEDIA_ROOT, pk, "pengoutput")
    meme_plots = os.path.join(pk, "pengoutput", "meme_plots")
    meme_motifs = load_meme_ids(peng_path)
    # meme_meta_info_list = Meme.fromfile(os.path.join(peng_meme_directory(pk), "out.meme"))
    meme_meta_info_list = Meme.fromfile(os.path.join(peng_path, "out.meme"))
    database = 100
    db = get_object_or_404(DbParameter, pk=database)
    db_dir = os.path.join(db.base_dir, 'Results')

    print(meme_plots)
    if result.complete:
        print("status is successfull")
        num_logos = range(1, (min(2, result.model_Order)+1))
        if result.mode == "Prediction" or result.mode == "Compare":
            return render(request, 'results/peng_to_bamm_result_detail.html',
                          {'result': result, 'opath': opath,
                           'mode': result.mode,
                           'Output_filename': Output_filename,
                           'num_logos': num_logos,
                           'db_dir': db_dir,
                           'meme_logo_path': meme_plots,
                           'meme_motifs': meme_motifs,
                           'meme_meta_info': meme_meta_info_list,
                           })
        elif result.mode == "Occurrence":
            return redirect('result_occurrence', result.mode, pk)

    else:
        print('status not ready yet')
        log_file = get_log_file(pk)
        command = "tail -20 %r" % log_file
        output = os.popen(command).read()
        return render(request, 'results/result_status.html',
                      {'result': result, 'opath': opath, 'output': output})

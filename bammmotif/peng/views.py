import os
import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from utils import deprecated
from bammmotif.peng.peng_to_bamm_form import PengToBammForm
from bammmotif.peng.form import get_valid_peng_form, get_valid_peng_form_meta, PengExampleForm, PengForm, PengFormMeta
from bammmotif.peng.job import create_job, validate_input_data, init_job, create_job_meta, create_bamm_job
from bammmotif.peng.tasks import run_peng, plot_meme, peng_chain
import bammmotif.bamm.tasks as bamm_tasks
from bammmotif.peng.utils import (
    upload_example_fasta_for_peng,
    copy_peng_to_bamm,
    load_meme_ids,
    check_if_request_from_peng_directly,
    save_selected_motifs,
    upload_example_fasta,
    read_bmscore,
    merge_meme_and_bmscore
)
from bammmotif.models import Job, PengJob_deprecated, DbParameter, Peng, JobInfo, Bamm
from bammmotif.forms import FindForm
from bammmotif.peng.job import file_path_peng
from bammmotif.peng_utils import get_motif_ids
from bammmotif.command_line import PlotMeme
from bammmotif.utils.meme_reader import Meme, split_meme_file, get_n_motifs
from bammmotif.utils import (
    get_log_file,
    get_user, set_job_name, valid_uuid,
    get_result_folder
)
import bammmotif.tasks as tasks
from bammmotif.peng.settings import (
    MEME_PLOT_DIRECTORY,
    NOT_ENOUGH_MOTIFS_SELECTED_FOR_REFINEMENT,
    get_meme_result_file_path,
    get_plot_output_directory,
    get_temporary_job_dir,
    get_bmscore_filename,
    FILTERPWM_INPUT_FILE,
    peng_meme_directory,
    get_peng_output_in_bamm_directory,
    get_memeplot_directory_in_bamm,
    get_bmscore_path,
    get_memeplot_directory_without_prefix,
)
import uuid

@deprecated
def peng_result_detail_deprecated(request, pk):
    result = get_object_or_404(PengJob_deprecated, pk=pk)
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

def peng_result_detail(request, pk):
    result = get_object_or_404(Peng, pk=pk)
    if result.job_id.complete:
        print("status is successfull")
        meme_result_file_path = get_meme_result_file_path(result.job_id.job_id)
        plot_output_directory = get_plot_output_directory(result.job_id.job_id)
        opath = os.path.join(get_result_folder(str(result.job_id)), MEME_PLOT_DIRECTORY).split('/', maxsplit=1)[1]
        bmf_name = os.path.join( get_temporary_job_dir(result.job_id.job_id), get_bmscore_filename(result.job_id.job_id, Peng))
        bm_scores = read_bmscore(bmf_name)
        if not os.path.exists(plot_output_directory):
            os.makedirs(plot_output_directory)
        meme_meta_info_list = Meme.fromfile(meme_result_file_path)
        meme_meta_info_list_old = Meme.fromfile(os.path.join(peng_meme_directory(str(pk)), FILTERPWM_INPUT_FILE))
        # add ausfc data to motifs
        meme_meta_info_list_new = merge_meme_and_bmscore(meme_meta_info_list, meme_meta_info_list_old, bm_scores)
        return render(request, 'results/peng_result_detail.html',
                      {'result': result,
                       'job_info': result.job_id,
                       'mode': result.job_id.mode,
                       'opath': opath,
                       'meme_meta_info': meme_meta_info_list_new,
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
        form, valid, args = get_valid_peng_form_meta(request.POST, request.FILES, request.user, mode)
        if not valid:
            print("FORM IS NOT VALID!!!!!")
            # TODO: Reload page here.
            pass
            # return render(request, 'job/de_novo_search.html', args)
        peng_job = create_job_meta(form, request, "peng", True)
        if mode == "example":
            upload_example_fasta(peng_job.job_id.job_id)
            peng_job = get_object_or_404(Peng, pk=peng_job.job_id.job_id)
            print("Example uploaded")
        ret, valid_input = validate_input_data(peng_job)
        # TODO: Adjust this part.
        if not valid_input:
            Job.objects.filter(job_id=peng_job).delete()
            # Job.objects.filter(job_ID=peng_job.pk).delete()
            # return render(request, 'job/de_novo_search.html', {'form': PengForm(), 'type': "Fasta", 'message': ret})
        if mode == 'example':
            upload_example_fasta_for_peng(peng_job.job_id)
        from bammmotif.peng.settings import get_temporary_job_dir
        print(get_temporary_job_dir(peng_job.job_id.job_id))
        peng_chain.delay(peng_job.job_id.job_id)
        return render(request, 'job/peng_bamm_split_submitted.html', {'pk': peng_job.job_id.job_id})
    if mode == 'example':
        form = PengExampleForm()
    else:
        form = PengFormMeta()
    print("Request IS NOT POST -> make form and redirect")
    return render(request, 'job/peng_bamm_split_peng_input.html',
                  {'form': form, 'mode': mode})

@deprecated
def run_peng_view_deprecated(request, mode='normal'):
    print("ENTERING Data PREDICT VIEW data_peng_changed: ", request.method, mode)
    if request.method == "POST":
        print("run_peng_view: Request IS POST")
        print(request.__dir__())
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
    if request.user.is_authenticated:
        user_jobs = PengJob_deprecated.objects.filter(user=request.user.id)
        return render(request, 'results/peng_result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_peng_results')

def peng_result_overview(request, pk):
    if request.user.is_authenticated:
        user_jobs = Peng.objects.filter(user=request.user.id)
        return render(request, 'results/peng_result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_peng_results')

def peng_load_bamm(request, pk):
    mode = "peng_to_bamm"
    peng_job = get_object_or_404(Peng, pk=pk)
    inputfile = str(peng_job.fasta_file).rsplit('/', maxsplit=1)[1]
    print("peng_load_bamm")
    if request.method == "POST":
        # TODO: Maybe do that differently.
        if check_if_request_from_peng_directly(request):
            at_least_one_motif_selected = save_selected_motifs(request.POST, pk)
            if not at_least_one_motif_selected:
                opath = os.path.join(get_result_folder(str(peng_job.job_id)), MEME_PLOT_DIRECTORY).split('/', maxsplit=1)[1]
                meme_result_file_path = get_meme_result_file_path(peng_job.job_id.job_id)
                meme_meta_info_list = Meme.fromfile(meme_result_file_path)
                return render(request, 'results/peng_result_detail.html',
                      {'result': peng_job,
                       'job_info': peng_job.job_id,
                       'mode': peng_job.job_id.mode,
                       'opath': opath,
                       'meme_meta_info': meme_meta_info_list,
                       'err_msg': NOT_ENOUGH_MOTIFS_SELECTED_FOR_REFINEMENT
                       })
            form = PengToBammForm()
            print("request from peng directly")
            return render(request, 'job/peng_bamm_split_peng_to_bamm.html',
                          {'form': form, 'mode': mode, 'inputfile': inputfile, 'job_name': peng_job.job_id.job_name, 'pk': peng_job.job_id.pk})
        form = PengToBammForm(request.POST, request.FILES)
        if form.is_valid():
            bamm_job = create_bamm_job('bamm', request, form, peng_job)
            ## Copy necessary files from last peng job.
            copy_peng_to_bamm(peng_job.job_id.job_id, bamm_job.job_id.job_id, request.POST)
            bamm_tasks.build_and_exec_chain.delay(bamm_job.job_id.job_id)
            return render(request, 'job/peng_to_bamm_submitted.html', {'pk': bamm_job.job_id.job_id})
        else:
            print("peng_load_bamm: Form is invalid!")
    form = PengToBammForm()
    return render(request, 'job/peng_bamm_split_peng_to_bamm.html',
                  {'form': form, 'mode': mode, 'inputfile': inputfile, 'job_name': peng_job.job_name, 'pk': pk})

@deprecated
def peng_load_bamm_deprecated(request, pk):
    mode = "peng_to_bamm"
    peng_job = get_object_or_404(PengJob_deprecated, pk=pk)
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
    if request.user.is_authenticated:
        user_jobs = Job.objects.filter(user=request.user.id)
        return render(request, 'results/peng_to_bamm_result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_peng_to_bamm_results')

def peng_to_bamm_result_detail(request, pk):
    result = get_object_or_404(Bamm, pk=pk)
    print(result.job_id.job_name)
    opath = get_result_folder(pk)
    Output_filename = result.Output_filename()
    if result.job_id.complete:
        peng_path = get_peng_output_in_bamm_directory(result.job_id.job_id)
        meme_plots = get_memeplot_directory_without_prefix(result.job_id.job_id)
        meme_motifs = load_meme_ids(peng_path)
        meme_meta_info_list = Meme.fromfile(os.path.join(peng_path, "out.meme"))
        bm_scores = read_bmscore(get_bmscore_path(result.peng))
        meme_meta_info_list_old = Meme.fromfile(os.path.join(peng_meme_directory(result.peng.job_id.job_id), FILTERPWM_INPUT_FILE))
        # add ausfc data to motifs
        meme_meta_info_list_new = merge_meme_and_bmscore(meme_meta_info_list, meme_meta_info_list_old, bm_scores)
        database = 100
        db = get_object_or_404(DbParameter, pk=database)
        db_dir = os.path.join(db.base_dir, 'Results')

        print(meme_plots)
        print("status is successfull")
        num_logos = range(1, (min(2, result.model_Order)+1))
        print(result.job_id.mode)
        if result.job_id.mode == "Prediction" or result.job_id.mode == "Compare":
            return render(request, 'results/peng_to_bamm_result_detail.html',
                          {'result': result, 'opath': opath,
                           'mode': result.job_id.mode,
                           'Output_filename': Output_filename,
                           'num_logos': num_logos,
                           'db_dir': db_dir,
                           'meme_logo_path': meme_plots,
                           'meme_motifs': meme_motifs,
                           'meme_meta_info': meme_meta_info_list_new,
                           })
        elif result.job_id.mode == "Occurrence":
            return redirect('result_occurrence', result.job_id.mode, pk)

    else:
        print('status not ready yet')
        log_file = get_log_file(pk)
        command = "tail -20 %r" % log_file
        output = os.popen(command).read()
        return render(request, 'results/result_status.html',
                      {'result': result, 'opath': opath, 'output': output})

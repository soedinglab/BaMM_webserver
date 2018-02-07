from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from .models import (
    ChIPseq, DbParameter
)
"""
from .forms import (
    PredictionForm, PredictionExampleForm,
    OccurrenceForm, OccurrenceExampleForm,
    OccurrenceDBForm,
    CompareForm, CompareExampleForm,
    FindForm
)
"""
from .tasks import (
    run_bamm, run_bammscan,
    run_peng
)
from .utils import (
    get_user, set_job_name, upload_example_fasta,
    upload_example_motif, 
    upload_db_input, valid_uuid
)
from .utils.path_helpers import (
    get_log_file,
    get_result_folder,
)
from bammmotif.models import JobInfo
from bammmotif.utils.misc import url_prefix
from .forms import FindForm
import datetime
import os
from os import path
from os.path import basename
from urllib.parse import urljoin


# #########################
# ## HOME and GENERAL VIEWS #########################


def home(request):
    return render(request, 'home/home.html')


def info(request):
    return render(request, 'home/aboutBaMMmotif.html')


def documentation(request):
    return render(request, 'home/documentation.html')


def download(request):
    return render(request, 'home/download.html')


def contact(request):
    return render(request, 'home/contact.html')


def imprint(request):
    return render(request, 'home/imprint.html')


# #########################
# ## JOB RELATED VIEWS
# #########################


def run_bammscan_view(request, mode='normal', pk='null'):
    if request.method == "POST":
        if mode == 'example':
            form = OccurrenceExampleForm(request.POST, request.FILES)
        if mode == 'db':
            form = OccurrenceDBForm(request.POST, request.FILES)
        if mode == 'normal':
            form = OccurrenceForm(request.POST, request.FILES)
        if form.is_valid():
            # read in data and parameter
            job = form.save(commit=False)
            job.created_at = datetime.datetime.now()
            job.user = get_user(request)
            job.mode = "Occurrence"
            job.save()
            job_pk = job.job_ID

            if job.job_name is None:
                set_job_name(job_pk)
                job = get_object_or_404(Job, pk = job_pk)

            # if example is requested, load the sampleData
            if mode == 'example':
                upload_example_fasta(job_pk)
                job = get_object_or_404(Job, pk = job_pk)
                upload_example_motif(job_pk)
                job = get_object_or_404(Job, pk = job_pk)

            # enter db input
            if mode == 'db':
                upload_db_input(job_pk, pk)
                job = get_object_or_404(Job, pk = job_pk)

            job = get_object_or_404(Job, pk = job_pk)

            run_bammscan.delay(job_pk)
            return render(request, 'job/submitted.html', {'pk': job_pk})
        else:
            print('POST Form is not valid!')
    if mode == 'db':
        form = OccurrenceDBForm()
        db_entry = get_object_or_404(ChIPseq, pk=pk)
        return render(request, 'job/bammscan_input.html',
                      {'form': form, 'mode': mode, 'pk': pk,
                       'db_entry': db_entry})
    if mode == 'example':
        form = OccurrenceExampleForm()
    if mode == 'normal':
        form = OccurrenceForm()
    return render(request, 'job/bammscan_input.html',
                  {'form': form, 'mode': mode})


def run_bamm_view(request, mode='normal'):
    if request.method == "POST":
        if mode == 'example':
            form = PredictionExampleForm(request.POST, request.FILES)
        else:
            print('store normal form')
            form = PredictionForm(request.POST, request.FILES)
        if form.is_valid():
            # read in data and parameter
            job = form.save(commit=False)
            job.created_at = datetime.datetime.now()
            job.user = get_user(request)
            job.mode = "Prediction"
            job.save()
            job_pk = job.job_ID

            if job.job_name is None:
                set_job_name(job_pk)
                job = get_object_or_404(Job, pk = job_pk)

            # if example is requested, load the sampleData
            if mode == 'example':
                upload_example_fasta(job_pk)
                job = get_object_or_404(Job, pk = job_pk)
                upload_example_motif(job_pk)
                job = get_object_or_404(Job, pk = job_pk)

            job = get_object_or_404(Job, pk = job_pk)
            if job.Motif_Initialization == 'PEnGmotif':
                run_peng.delay(job_pk)
            else:
                run_bamm.delay(job_pk)

            return render(request, 'job/submitted.html', {'pk': job_pk})

    if mode == 'example':
        form = PredictionExampleForm()
    else:
        form = PredictionForm()
    return render(request, 'job/bamm_input.html',
                  {'form': form, 'mode': mode})


def submitted(request, pk):
    return render(request, 'job/submitted.html', {'pk': pk})


# #########################
# ## RESULT RELATED VIEWS
# #########################


#def find_results(request):
#    if request.method == "POST":
#        form = FindForm(request.POST)
#        if form.is_valid():
#            jobid = form.cleaned_data['job_ID']
#            if valid_uuid(jobid):
#                if Job.objects.filter(pk=jobid).exists():
#                    return redirect('result_detail', pk=jobid)
#            form = FindForm()
#            return render(request, 'results/results_main.html', {'form': form, 'warning': True})
#    else:
#        form = FindForm()
#    return render(request, 'results/results_main.html', {'form': form, 'warning': False})

def find_results(request):
    if request.method == "POST":
        form = FindForm(request.POST)
        if form.is_valid():
            jobid = form.cleaned_data['job_ID']
            meta_job = get_object_or_404(JobInfo, job_id=jobid)
            base = request.build_absolute_uri('/')
            url = urljoin(base, url_prefix[meta_job.job_type] + jobid)
            return redirect(url, permanent=True)
    return render(request, 'results/results_main.html', {'form': FindForm()})


def result_overview(request):
    if request.user.is_authenticated():
        user_jobs = Job.objects.filter(user=request.user.id)
        return render(request, 'results/result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_results')


def delete(request, pk):
    Job.objects.filter(job_ID=pk).delete()
    if request.user.is_authenticated():
        user_jobs = Job.objects.filter(user=request.user.id)
        return render(request, 'results/result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_results')


def result_detail(request, pk):
    result = get_object_or_404(Job, pk=pk)
    opath = get_result_folder(pk)
    if basename(os.path.splitext(result.Input_Sequences.name)[0]) == '':
        outname = basename(os.path.splitext(result.Motif_InitFile.name)[0])
    else:
        outname = basename(os.path.splitext(result.Input_Sequences.name)[0])

    database = 100
    db = get_object_or_404(DbParameter, pk=database)
    db_dir = path.join(db.base_dir, 'Results')

    if result.complete:
        print("status is successfull")
        num_logos = range(1, (min(3,result.model_Order+1)))
        return render(request, 'results/result_detail.html',
                      {'result': result, 'opath': opath,
                       'mode': result.mode,
                       'Output_filename': outname,
                       'num_logos': num_logos,
                       'db_dir': db_dir})
    else:
        print('status not ready yet')
        log_file = get_log_file(pk)
        command = "tail -20 %r" % log_file
        output = os.popen(command).read()
        return render(request, 'results/result_status.html',
                      {'job_ID': result.job_ID, 'job_name': result.job_name, 'status': result.status, 'output': output})

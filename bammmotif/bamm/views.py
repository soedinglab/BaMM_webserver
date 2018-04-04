import datetime
import os
from os import path
from os.path import basename
import itertools

from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.conf import settings

from ..models import (
    ChIPseq, DbParameter, BaMMJob, JobInfo
)

from ..utils import (
    get_log_file,
    get_result_folder,
)

from ..forms import MetaJobNameForm
from . import forms as bamm_forms

from bammmotif.utils import (
    get_user, set_job_name, upload_example_fasta,
    upload_example_motif,
    upload_db_input, valid_uuid
)
from bammmotif.peng.job import init_job


def one_step_denovo(request, mode='normal'):
    max_file_size = settings.MAX_UPLOAD_FILE_SIZE
    if request.method == 'POST':
        pass
    else:
        metajob_form = MetaJobNameForm()
        job_form = bamm_forms.OneStepBammJobForm()
        return render(
            request, 'denovo/one_step_denovo.html',
            {
                'metajob_form': metajob_form,
                'job_form': job_form,
                'max_file_size': max_file_size,
                'all_form_fields': itertools.chain(metajob_form, job_form),
                'mode': mode,
            }
        )


# #########################
# ## JOB RELATED VIEWS
# #########################


def run_compare_view(request, mode='normal'):
    if request.method == "POST":
        if mode == 'example':
            form = CompareExampleForm(request.POST, request.FILES)
        else:
            print('store normal form')
            form = CompareForm(request.POST, request.FILES)
        if form.is_valid():
            # read in data and parameter
            job = form.save(commit=False)
            job.created_at = datetime.datetime.now()
            job.user = get_user(request)
            job.mode = "Compare"
            job.save()
            job_pk = job.job_ID

            if job.job_id.job_name is None:
                set_job_name(job_pk)
                job = get_object_or_404(Job, pk = job_pk)

            # if example is requested, load the sampleData
            if mode == 'example':
                #upload_example_fasta(job_pk)
                #job = get_object_or_404(Job, pk = job_pk)
                upload_example_motif(job_pk)
                job = get_object_or_404(Job, pk = job_pk)

            job = get_object_or_404(Job, pk = job_pk)
            job.FDR = False
            job.score_Seqset = False
            job.MMcompare = True
            job.save()
            run_compare.delay(job_pk)
            return render(request, 'job/submitted.html', {'pk': job_pk})

    if mode == 'example':
        form = CompareExampleForm()
    else:
        form = CompareForm()
    return render(request, 'job/compare_input.html',
                  {'form': form, 'mode': mode})


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
            job_info = init_job('bamm')
            job_info.created_at = datetime.datetime.now()
            job_info.user = get_user(request)
            job_info.mode = "Prediction"
            job_info.save()
            # read in data and parameter
            bamm_job = form.save(commit=False)
            bamm_job.job_id = job_info
            bamm_job.save()
            job_pk = bamm_job.job_id.job_id

            if bamm_job.job_id.job_name is None:
                set_job_name(job_pk)
                bamm_job = get_object_or_404(Bamm, pk=job_pk)

            # if example is requested, load the sampleData
            if mode == 'example':
                upload_example_fasta(job_pk)
                bamm_job = get_object_or_404(Bamm, pk=job_pk)
                upload_example_motif(job_pk)
                bamm_job = get_object_or_404(Bamm, pk=job_pk)

            bamm_job = get_object_or_404(Bamm, pk = job_pk)
            build_and_exec_chain.delay(job_pk)
            #if bamm_job.Motif_Initialization == 'PEnGmotif':
            #    run_peng.delay(job_pk)
            #else:
            #    run_bamm.delay(job_pk)

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


def find_results(request):
    if request.method == "POST":
        form = FindForm(request.POST)
        if form.is_valid():
            jobid = form.cleaned_data['job_ID']
            if valid_uuid(jobid):
                if Bamm.objects.filter(pk=jobid).exists():
                    return redirect('result_detail', pk=jobid)
            form = FindForm()
            return render(request, 'results/results_main.html', {'form': form, 'warning': True})
    else:
        form = FindForm()
    return render(request, 'results/results_main.html', {'form': form, 'warning': False})


def result_overview(request):
    if request.user.is_authenticated():
        user_jobs = Job.objects.filter(user=request.user.id)
        return render(request, 'results/result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_results')


def delete(request, pk):
    JobInfo.objects.filter(job_id=pk).delete()
    if request.user.is_authenticated():
        user_jobs = Job.objects.filter(user=request.user.id)
        return render(request, 'results/result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_results')


def result_detail(request, pk):
    result = get_object_or_404(Bamm, pk=pk)
    opath = get_result_folder(pk)
    if basename(os.path.splitext(result.Input_Sequences.name)[0]) == '':
        outname = basename(os.path.splitext(result.Motif_InitFile.name)[0])
    else:
        outname = basename(os.path.splitext(result.Input_Sequences.name)[0])

    database = 100
    db = get_object_or_404(DbParameter, pk=database)
    db_dir = path.join(db.base_dir, 'Results')

    if result.job_id.complete:
        print("status is successfull")
        num_logos = range(1, (min(3,result.model_Order+1)))
        return render(request, 'results/result_detail.html',
                      {'result': result, 'opath': opath,
                       'mode': result.job_id.mode,
                       'Output_filename': outname,
                       'num_logos': num_logos,
                       'db_dir': db_dir})
    else:
        print('status not ready yet')
        log_file = get_log_file(pk)
        command = "tail -20 %r" % log_file
        output = os.popen(command).read()
        return render(request, 'results/result_status.html',
                      {'job_ID': result.job_id.job_id, 'job_name': result.job_id.job_name, 'status': result.job_id.status, 'output': output})



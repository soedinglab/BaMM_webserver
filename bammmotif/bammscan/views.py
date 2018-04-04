from os import path
import os
import itertools

from django.shortcuts import get_object_or_404, render
from django.db import transaction
from django.conf import settings


from ..models import ChIPseq
from ..forms import MetaJobNameForm

from ..utils import (
    get_user,
    set_job_name_if_unset,
    get_log_file,
    get_result_folder,
    upload_example_fasta,
    upload_example_motif,
    register_job_session,
    check_motif_input,
)

from .forms import (
    BaMMScanExampleForm,
    BaMMScanDBForm,
    BaMMScanForm
)
from .models import BaMMScanJob
from .tasks import bamm_scan_pipeline
from .utils import upload_db_motif


def run_bammscan_view(request, mode='normal', pk='null'):
    if request.method == "POST":
        meta_job_form = MetaJobNameForm(request.POST)
        if mode == 'example':
            form = BaMMScanExampleForm(request.POST, request.FILES)
        elif mode == 'db':
            form = BaMMScanDBForm(request.POST, request.FILES)
            motif = get_object_or_404(ChIPseq, pk=pk)
        elif mode == 'normal':
            form = BaMMScanForm(request.POST, request.FILES)

        is_valid = form.is_valid() and meta_job_form.is_valid()
        if is_valid:
            meta_job = meta_job_form.save(commit=False)
            meta_job.user = get_user(request)
            meta_job.mode = "BaMMScan"
            meta_job.job_type = 'bammscan'
            set_job_name_if_unset(meta_job)
            meta_job.save()

            job = form.save(commit=False)
            job.meta_job = meta_job
            job_pk = meta_job.pk

            # if example is requested, load the sampleData
            if mode == 'example':
                upload_example_fasta(job)
                upload_example_motif(job)
            # enter db input
            elif mode == 'db':
                upload_db_motif(job, motif)

            is_valid = check_motif_input(job, form)

            if is_valid:
                with transaction.atomic():
                    job.meta_job.save()
                    register_job_session(request, job.meta_job)
                    job.save()

                bamm_scan_pipeline.delay(job_pk)
                return render(request, 'job/submitted.html', {
                    'pk': job_pk,
                    'result_target': 'scan_results',
                })

    else:
        is_valid = True
        meta_job_form = MetaJobNameForm()
        if mode == 'example':
            form = BaMMScanExampleForm()
        elif mode == 'normal':
            form = BaMMScanForm()
        elif mode == 'db':
            form = BaMMScanDBForm()
            db_entry = get_object_or_404(ChIPseq, pk=pk)
            return render(request, 'bammscan/bammscan_input.html', {
                'form': form,
                'mode': mode,
                'pk': pk,
                'db_entry': db_entry,
            })

    return render(request, 'bammscan/bammscan_input.html', {
        'job_form': form,
        'metajob_form': meta_job_form,
        'mode': mode,
        'all_form_fields': itertools.chain(form, meta_job_form),
        'max_file_size': settings.MAX_UPLOAD_FILE_SIZE,
        'validation_errors': not is_valid,
    })


def result_details(request, pk):
    result = get_object_or_404(BaMMScanJob, pk=pk)
    meta_job = result.meta_job
    opath = get_result_folder(pk)
    filename_prefix = result.filename_prefix

    motif_db = result.motif_db
    db_dir = motif_db.relative_db_model_dir

    if meta_job.complete:
        num_logos = range(1, (min(3, result.model_order+1)))
        return render(request, 'bammscan/result_detail.html', {
            'sequence_fname': path.basename(result.Input_Sequences.name),
            'motif_fname': path.basename(result.Motif_InitFile.name),
            'result': result,
            'opath': opath,
            'mode': meta_job.mode,
            'Output_filename': filename_prefix,
            'num_logos': num_logos,
            'db_dir': db_dir})
    else:
        log_file = get_log_file(pk)
        command = "tail -20 %r" % log_file
        output = os.popen(command).read()
        return render(request, 'results/result_status.html', {
            'job_id': pk,
            'job_name': meta_job.job_name,
            'status': meta_job.status,
            'output': output
        })

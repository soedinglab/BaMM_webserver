from os import path
import os

from django.utils import timezone
from django.shortcuts import get_object_or_404, render
from django.db import transaction

from .forms import (
    BaMMScanExampleForm,
    BaMMScanDBForm,
    BaMMScanForm
)
from ..forms import MetaJobNameForm

from ..utils import (
    get_user,
    set_job_name,
    get_log_file,
    get_result_folder,
    upload_example_fasta,
    upload_example_motif,
)

from .models import BaMMScanJob

from .tasks import bamm_scan_pipeline


def run_bammscan_view(request, mode='normal', pk='null'):
    if request.method == "POST":
        meta_job_form = MetaJobNameForm(request.POST)
        if mode == 'example':
            form = BaMMScanExampleForm(request.POST, request.FILES)
        elif mode == 'db':
            form = BaMMScanDBForm(request.POST, request.FILES)
        elif mode == 'normal':
            form = BaMMScanForm(request.POST, request.FILES)

        if form.is_valid() and meta_job_form.is_valid():
            meta_job = meta_job_form.save(commit=False)
            meta_job.created_at = timezone.now()
            meta_job.user = get_user(request)
            meta_job.mode = "BaMMScan"
            meta_job.save()

            if meta_job.job_name is None:
                job_id_short = str(meta_job).split("-", maxsplit=1)
                meta_job.job_name = job_id_short[0]

            job = form.save(commit=False)
            job.meta_job = meta_job
            job_pk = meta_job.pk

            # if example is requested, load the sampleData
            if mode == 'example':
                upload_example_fasta(job)
                upload_example_motif(job)

            # enter db input
            if mode == 'db':
                pass
                # this is currently not implemented

            with transaction.atomic():
                job.meta_job.save()
                job.save()

            bamm_scan_pipeline.delay(job_pk)
            return render(request, 'job/submitted.html', {
                'pk': job_pk,
                'result_target': 'scan_results',
            })

    meta_job_form = MetaJobNameForm()
    if mode == 'example':
        form = BaMMScanExampleForm()
    if mode == 'normal':
        form = BaMMScanForm()
    return render(request, 'job/bammscan_input.html',
                  {
                      'form': form,
                      'mode': mode,
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

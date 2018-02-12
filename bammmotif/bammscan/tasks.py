from contextlib import redirect_stdout, redirect_stderr

import celery
from celery import task
from django.shortcuts import get_object_or_404

from bammmotif.bamm import tasks as bamm_tasks

from ..utils import (
    JobSaveManager,
    make_job_folder,
    get_log_file,
)
from .models import BaMMScanJob
from ..mmcompare.tasks import generic_mmcompare_task, generic_mmcompare_import_matches
from ..tasks import generic_model_zip_task
from .commands import BaMMScan


def generic_bammscan_task(job, first_in_pipeline, is_refined_model):
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        # first define log file for redirecting output information
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f), redirect_stderr(f):
                BaMMScan(job, first_in_pipeline, is_refined_model)


@task(bind=True)
def bamm_scan_pipeline(self, job_pk):
    job = get_object_or_404(BaMMScanJob, meta_job__pk=job_pk)
    make_job_folder(job_pk)
    pipeline_tasks = [
        bamm_scan_task.si(job_pk)
    ]
    if job.FDR:
        pipeline_tasks.append(fdr_task.si(job_pk))
    if job.MMcompare:
        pipeline_tasks.append(mmcompare_task.si(job_pk))
        pipeline_tasks.append(import_mmcompare_hits.si(job_pk))
    pipeline_tasks.append(compress_task.si(job_pk))
    pipeline_tasks.append(mmcompare_finalize.si(job_pk))

    celery.chain(pipeline_tasks)()


@task(bind=True)
def bamm_scan_task(self, job_pk):
    job = get_object_or_404(BaMMScanJob, meta_job__pk=job_pk)
    generic_bammscan_task(job, first_in_pipeline=True, is_refined_model=False)


@task(bind=True)
def fdr_task(self, job_pk):
    job = get_object_or_404(BaMMScanJob, meta_job__pk=job_pk)
    bamm_tasks.generic_fdr_task(job, first_in_pipeline=False, is_refined=False)


@task(bind=True)
def mmcompare_task(self, job_pk):
    job = get_object_or_404(BaMMScanJob, meta_job__pk=job_pk)
    generic_mmcompare_task(job)


@task(bind=True)
def compress_task(self, job_pk):
    job = get_object_or_404(BaMMScanJob, meta_job__pk=job_pk)
    generic_model_zip_task(job)


@task(bind=True)
def mmcompare_finalize(self, job_pk):
    job = get_object_or_404(BaMMScanJob, meta_job__pk=job_pk)
    job.meta_job.complete = True
    job.meta_job.save()


@task(bind=True)
def import_mmcompare_hits(self, job_pk):
    job = get_object_or_404(BaMMScanJob, meta_job__pk=job_pk)
    generic_mmcompare_import_matches(job)

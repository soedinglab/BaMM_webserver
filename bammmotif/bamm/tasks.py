from __future__ import absolute_import

import logging
from contextlib import redirect_stdout, redirect_stderr


from celery import task, chain
from django.shortcuts import get_object_or_404

from ..utils import (
    JobSaveManager,
    get_log_file,
    make_job_folder,
)
from ..commands import Compress
from ..bammscan.tasks import generic_bammscan_task
from ..mmcompare.tasks import generic_mmcompare_task

from .commands import (
    BaMM, FDR,
)
from .models import BaMMJob


logger = logging.getLogger(__name__)


# Don't use that yet.
class ChainBuilder:

    def __init__(self, job_pk, initializer, finalizer):
        self._job_pk = job_pk
        self._initializer = initializer
        self._finalizer = finalizer
        self._task_list = []

    @property
    def next(self):
        return None

    @next.setter
    def next(self, _task):
        self._task_list.append(_task.si(self._job_pk))

    def pop(self):
        self._task_list.pop()

    def __enter__(self):
        self._task_list.append(self._initializer.si(self._job_pk))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._task_list.append(self._finalizer.si(self._job_pk))
        ret = chain(*self._task_list)()
        return True


def generic_compress_task(job):
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f):
                Compress(job)


def generic_bamm_task(job, first_in_pipeline, is_refined):
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f), redirect_stderr(f):
                    BaMM(job, first_in_pipeline, is_refined)


def generic_fdr_task(job, first_in_pipeline, is_refined):
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        # first define log file for redirecting output information
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f), redirect_stderr(f):
                FDR(job, first_in_pipeline, is_refined)


@task(bind=True)
def bamm_refinement_pipeline(self, job_pk):
    job = get_object_or_404(BaMMJob, meta_job__pk=job_pk)
    job_pk = job.meta_job.pk
    make_job_folder(job_pk)

    pipeline = [
        bamm_task.si(job_pk)
    ]
    if job.score_Seqset:
        pipeline.append(bammscan_task.si(job_pk))
    if job.FDR:
        pipeline.append(fdr_task.si(job_pk))
    if job.MMcompare:
        pipeline.append(mmcompare_task.si(job_pk))
    pipeline.append(compress_task.si(job_pk))
    pipeline.append(finalize.si(job_pk))

    chain(pipeline)()


@task(bind=True)
def bamm_task(self, job_pk):
    job = get_object_or_404(BaMMJob, meta_job__pk=job_pk)
    generic_bamm_task(job, first_in_pipeline=True, is_refined=False)


@task(bind=True)
def bammscan_task(self, job_pk):
    job = get_object_or_404(BaMMJob, meta_job__pk=job_pk)
    generic_bammscan_task(job, first_in_pipeline=False, is_refined_model=True)


@task(bind=True)
def fdr_task(self, job_pk):
    job = get_object_or_404(BaMMJob, meta_job__pk=job_pk)
    generic_fdr_task(job, first_in_pipeline=False, is_refined=False)


@task(bind=True)
def mmcompare_task(self, job_pk):
    job = get_object_or_404(BaMMJob, meta_job__pk=job_pk)
    generic_mmcompare_task(job)


@task(bind=True)
def compress_task(self, job_pk):
    job = get_object_or_404(BaMMJob, meta_job__pk=job_pk)
    generic_compress_task(job)


@task(bind=True)
def finalize(self, job_pk):
    job = get_object_or_404(BaMMJob, meta_job__pk=job_pk)
    job.meta_job.complete = True
    job.meta_job.save()

from __future__ import absolute_import
from contextlib import redirect_stdout, redirect_stderr
import shutil

from celery import task
from django.conf import settings
from django.utils import timezone

from .commands import Compress
from .utils.path_helpers import (
    get_log_file,
    get_job_input_folder,
    get_job_folder,
)

from .models.models import JobInfo

from logging import getLogger

logger = getLogger(__name__)


def generic_model_zip_task(job):
    job_pk = job.meta_job.pk
    logfile = get_log_file(job_pk)
    with open(logfile, 'a') as f:
        with redirect_stdout(f), redirect_stderr(f):
            Compress(job)


@task
def cleanup_task():
    cleanup_expired_jobs()
    cleanup_input_files()


def cleanup_input_files():
    min_time = timezone.now() - timezone.timedelta(days=settings.MAX_INPUT_STORAGE_DAYS)
    timed_out_jobs = JobInfo.objects.filter(created_at__lt=min_time, has_input=True,
                                            is_example=False)

    for job in timed_out_jobs:
        logger.debug('Job %s selected for input cleanup.', job.job_id)
        input_folder = get_job_input_folder(job.job_id)
        job.has_input = False
        job.save()
        try:
            shutil.rmtree(input_folder)
        except FileNotFoundError:
            logger.warn('Could not find input folder %s', input_folder)

    logger.info('Cleaned up input files of %s jobs', len(timed_out_jobs))


def cleanup_expired_jobs():
    min_time = timezone.now() - timezone.timedelta(days=settings.MAX_JOB_STORAGE_DAYS)
    timed_out_jobs = JobInfo.objects.filter(created_at__lt=min_time, is_example=False)

    for job in timed_out_jobs:
        logger.debug('Job %s selected for removal.', job.job_id)
        job_folder = get_job_folder(job.job_id)
        job.delete()
        try:
            shutil.rmtree(job_folder)
        except FileNotFoundError:
            logger.warn('Could not find job folder %s', job_folder)

    logger.info('Removed %s expired jobs', len(timed_out_jobs))

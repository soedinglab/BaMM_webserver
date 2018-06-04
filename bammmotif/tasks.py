from __future__ import absolute_import
from contextlib import redirect_stdout, redirect_stderr
import shutil
import os

from celery import task
from django.conf import settings
from django.utils import timezone
from django.core import management

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
    management.call_command('cleanup')
    logger.info('automatic clean successful.')


@task
def full_backup():
    management.call_command('dbbackup', noinput=True)
    management.call_command('mediabackup', noinput=True, compress=True)
    logger.info('automatic backup successful.')

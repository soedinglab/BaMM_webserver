import shutil
import os
from logging import getLogger

from django.conf import settings
from django.utils import timezone

from ..models.models import JobInfo
from .path_helpers import (
    get_job_input_folder,
    get_job_folder,
)


logger = getLogger(__name__)


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
            logger.info('Could not find input folder %s', input_folder)

    logger.info('removed input files of %s jobs', len(timed_out_jobs))


def cleanup_expired_jobs():
    min_time = timezone.now() - timezone.timedelta(days=settings.MAX_JOB_STORAGE_DAYS)
    timed_out_jobs = JobInfo.objects.filter(created_at__lt=min_time, is_example=False)
    n_selected_jobs = len(timed_out_jobs)
    timed_out_jobs.delete()
    logger.info('removed %s expired jobs', n_selected_jobs)


def remove_orphan_jobdirs():
    job_ids = {str(job.job_id) for job in JobInfo.objects.all()}
    n_orphans = 0
    for job_dir in os.listdir(settings.JOB_DIR):
        if job_dir not in job_ids:
            try:
                full_job_dir_path = get_job_folder(job_dir)
                if not os.path.isdir(full_job_dir_path):
                    continue
                shutil.rmtree(full_job_dir_path)
                logger.debug('removing orphaned job folder: %s', full_job_dir_path)
                n_orphans += 1
            except OSError as exc:
                logger.error(exc)
    logger.info('removed %s orphaned job folders', n_orphans)


def full_cleanup():
    cleanup_expired_jobs()
    cleanup_input_files()
    remove_orphan_jobdirs()

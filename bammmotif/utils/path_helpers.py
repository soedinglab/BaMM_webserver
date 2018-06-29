from django.conf import settings

from os import path
import os
import logging

logger = logging.getLogger(__name__)


def get_result_folder(job_id):
    return path.join(settings.JOB_DIR_PREFIX, str(job_id), 'Output')


def get_job_folder(job_id):
    return path.join(settings.MEDIA_ROOT, settings.JOB_DIR_PREFIX, str(job_id))


def make_job_folder(job_id):
    job_folder = get_job_folder(job_id)
    output_dir = path.join(job_folder, 'Output')
    if not path.isdir(output_dir):
        os.makedirs(output_dir)
    return job_folder


def make_job_output_folder(job_id):
    job_output_folder = get_job_output_folder(job_id)
    if not path.isdir(job_output_folder):
        os.makedirs(job_output_folder)


def get_job_output_folder(job_id):
    return path.join(get_job_folder(job_id), 'Output')


def get_job_input_folder(job_id):
    return path.join(get_job_folder(job_id), 'Input')


def get_log_file(job_id):
    return path.join(get_job_folder(job_id), 'job.log')

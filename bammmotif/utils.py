from django.conf import settings
import sys
from os import path
import os
import datetime
import traceback
import subprocess


def get_job_folder(job_id):
    return path.join(settings.MEDIA_ROOT, settings.JOB_DIR_PREFIX, str(job_id))


def make_job_folder(job_id):
    job_folder = get_job_folder(job_id)
    if not path.isdir(job_folder):
        os.makedirs(job_folder)
    return job_folder


def get_job_output_folder(job_id):
    return path.join(get_job_folder(job_id), 'Output')


def get_job_input_folder(job_id):
    return path.join(get_job_folder(job_id), 'Input')


def get_log_file(job_id):
    return path.join(get_job_folder(job_id), 'job.log')


class JobSaveManager:

    def __init__(self, job, success_status='Success', error_status='Error'):
        self.error_status = error_status
        self.success_status = success_status
        self.job = job

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, tb):
        job = self.job
        if error_type is not None:
            job.status = self.error_status
            self.had_exception = True
            traceback.print_exception(error_type, error, tb, file=sys.stdout)
            print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status)
        else:
            job.status = self.success_status
            self.had_exception = False
            print(datetime.datetime.now(), "\t | END: \t %s " % job.status)
        job.save()
        return True


def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    while True:
        nextline = process.stdout.readline()
        if nextline == b'' and process.poll() is not None:
            break
        print(nextline.decode('utf-8'), file=sys.stdout, end='')
        sys.stdout.flush()
    process.wait()
    return process.returncode

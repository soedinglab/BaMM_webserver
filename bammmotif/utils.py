from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.files import File
from ipware.ip import get_ip
from .models import Job
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


def get_user(request):
    # assign user to new job instance
    if request.user.is_authenticated():
        return request.user
    else:
        ip = get_ip(request)
        if ip is not None:
            # check if anonymous user already exists
            anonymous_users = User.objects.filter(username=ip)
            if anonymous_users.exists():
                return get_object_or_404(User, username=ip)
            else:
                # create an anonymous user and log them in
                new_u = User(username=ip, first_name='Anonymous',
                             last_name='User')
                new_u.set_unusable_password()
                new_u.save()
                return new_u
        else:
            print("NO USER SETABLE")


def set_job_name(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    # truncate job_id
    job_id_short = str(job.job_ID).split("-", 1)
    job.job_name = job_id_short[0]
    job.save()


def upload_example_fasta(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    out_filename = "ExampleData.fasta"
    with open(settings.EXAMPLE_FASTA) as fh:
        job.Input_Sequences.save(out_filename, File(fh))
        job.save()


def upload_example_motif(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    out_filename = "ExampleMotif.meme"
    with open(settings.EXAMPLE_MOTIF) as fh:
        job.Motif_InitFile.save(out_filename, File(fh))
    job.Motif_Initialization = 'Custom File'
    job.Motif_Init_File_Format = 'PWM'
    job.save()

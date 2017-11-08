from __future__ import absolute_import
import os


from .utils import JobSaveManager, make_job_folder, get_log_file
from .commands import Compress
from celery import task
from celery import shared_task, task
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.files import File
from django.core.mail import send_mail
from django.contrib.auth.models import User
from ipware.ip import get_ip
from .models import Job, PengJob
from .command_line import ShootPengModule

from os.path import basename
from contextlib import redirect_stdout
import tempfile
import subprocess
import datetime
import os
import sys
import shutil

@task(bind=True)
def valid_init(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    try:
        job.status = 'Check Input File'
        job.save()
        check = subprocess.Popen(['/code/bammmotif/static/scripts/valid_Init',
                                  str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name)),
                                  str(os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)),
                                  str(job.Motif_Init_File_Format)],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check.wait()
        out, err = check.communicate()
        out = out.decode('ascii')
        if out == "OK":
            return 0
        else:
            return 1

    except Exception as e:
        job.status = 'error'
        job.save()
        return 1

@task(bind=True)
def valid_fasta(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    try:
        job.status = 'Check Input File'
        job.save()
        check = subprocess.Popen(['/code/bammmotif/static/scripts/valid_fasta',
                                  str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check.wait()

        out, err = check.communicate()
        out = out.decode('ascii')
        if out == "OK":
            return 0
        else:
            return 1

    except Exception as e:
        job.status = 'error'
        job.save()
        return 1

@task(bind=True)
def run_peng(self, job_pk):
    peng_job = get_object_or_404(PengJob, pk=job_pk)
    with JobSaveManager(peng_job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        print("logfile: ", logfile)
        peng = ShootPengModule.from_job(peng_job)
        peng.set_log_file(logfile)
        peng.run()
        # Compress(job_pk)
        peng_job.complete = True
    return 1 if mgr.had_exception else 0

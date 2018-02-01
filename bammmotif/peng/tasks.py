from __future__ import absolute_import

import subprocess
import os
from os import path

from celery import task, chain
from django.shortcuts import get_object_or_404
from django.conf import settings
from bammmotif.peng.settings import FASTA_VALIDATION_SCRIPT, MEME_PLOT_INPUT, JOB_OUTPUT_DIRECTORY
from bammmotif.peng_utils import get_motif_ids
from bammmotif.peng.settings import MEME_PLOT_DIRECTORY
from bammmotif.peng.utils import zip_motifs
from bammmotif.utils.meme_reader import Meme, split_meme_file


from ..models import JobInfo
from ..utils import (
    JobSaveManager,
    get_job_output_folder,
    get_result_folder,
    get_job_folder,
    make_job_folder,
    get_log_file,
)

from .models import PengJob
from .cmd_modules import (
    PlotMeme,
    FilterPWM,
    ShootPengModule,
)

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
        check = subprocess.Popen([FASTA_VALIDATION_SCRIPT,
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


def run_peng_generic(job):
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        # first define log file for redirecting output information
        logfile = get_log_file(job_pk)
        peng = ShootPengModule.from_job(job)
        peng.set_log_file(logfile)
        peng.run()


def run_pwm_filter_generic(job):
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        directory = path.join(get_job_output_folder(job_pk))
        fpwm = FilterPWM.init_with_extra_directory(directory)
        logfile = get_log_file(job_pk)
        fpwm.set_log_file(logfile)
        fpwm.run()


def run_meme_plotting_generic(job):
    job_pk = job.meta_job.pk
    meme_result_file_path = path.join(get_job_output_folder(job_pk), MEME_PLOT_INPUT)
    plot_output_directory = path.join(get_job_output_folder(job_pk), MEME_PLOT_DIRECTORY)
    if not path.exists(plot_output_directory):
        os.makedirs(plot_output_directory)
    motif_ids = get_motif_ids(meme_result_file_path)
    PlotMeme.plot_meme_list(motif_ids, meme_result_file_path, plot_output_directory)
    # Split one large meme to multiple smaller ones
    split_meme_file(meme_result_file_path, plot_output_directory)
    # Zip motifs
    zip_motifs(motif_ids, plot_output_directory, with_reverse=True)


@task(bind=True)
def peng_task(self, job_pk):
    job = get_object_or_404(PengJob, meta_job__pk=job_pk)
    run_peng_generic(job)


@task(bind=True)
def pwm_filter_task(self, job_pk):
    job = get_object_or_404(PengJob, meta_job__pk=job_pk)
    run_pwm_filter_generic(job)


@task(bind=True)
def meme_plotting_task(self, job_pk):
    job = get_object_or_404(PengJob, meta_job__pk=job_pk)
    run_meme_plotting_generic(job)


@task(bind=True)
def peng_seeding_pipeline(self, job_pk):
    job = get_object_or_404(PengJob, meta_job__pk=job_pk)
    job_pk = job.meta_job.pk
    make_job_folder(job_pk)
    pipeline = [
        peng_task.si(job_pk),
        pwm_filter_task.si(job_pk),
        meme_plotting_task.si(job_pk),
        finalize.si(job_pk),
    ]
    chain(pipeline)()


@task(bind=True)
def finalize(self, job_pk):
    job = get_object_or_404(PengJob, meta_job__pk=job_pk)
    job.meta_job.complete = True
    job.meta_job.save()

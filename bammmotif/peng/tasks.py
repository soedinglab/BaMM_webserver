from __future__ import absolute_import

import subprocess
import os
from os import path

from celery import task, chain
from django.shortcuts import get_object_or_404
from django.conf import settings
from bammmotif.peng.settings import FASTA_VALIDATION_SCRIPT, MEME_PLOT_INPUT, JOB_OUTPUT_DIRECTORY, PENG_PLOT_LOGO_ORDER
from bammmotif.peng.settings import MEME_PLOT_DIRECTORY
from .utils import (
    zip_motifs,
    rename_and_move_plots,
    rename_bamms,
    zip_bamm_motifs,
    get_motif_ids,
)
from bammmotif.utils.meme_reader import split_meme_file
from bammmotif.peng.io import (
        meme_plot_directory, 
        bamm_directory_old, 
        filter_output_file_old, 
        get_job_directory,
        get_temporary_job_dir
)

from ..utils import (
    JobSaveManager,
    get_job_output_folder,
    make_job_folder,
    get_log_file,
    run_command,
)
from ..utils.meme_reader import get_motif_ids

from .models import PengJob
from .cmd_modules import (
    PlotMeme,
    FilterPWM,
    ShootPengModule,
    ZipMotifs,
)


def run_peng_generic(job):
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        # first define log file for redirecting output information
        logfile = get_log_file(job_pk)
        peng = ShootPengModule.from_job(job)
        peng.temp_dir = get_temporary_job_dir(job_pk)
        peng.set_log_file(logfile)
        peng.run()


def run_pwm_filter_generic(job):
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        fpwm = FilterPWM()
        logfile = get_log_file(job_pk)
        fpwm.set_log_file(logfile)
        fpwm.input_file = job.meme_output
        fpwm.output_file = job.filtered_meme
        fpwm.run()
        n_motifs = len(get_motif_ids(job.filtered_meme))
        job.num_motifs = n_motifs


def convert_to_bamm_generic(job):
    target_dir = bamm_directory_old(job.meta_job.pk)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    input_file = job.filtered_meme
    run_command(['pwm2bamm.py', input_file, '-o', target_dir])
    rename_bamms(target_dir, input_file)


def run_meme_plotting_generic(job):
    job_pk = job.meta_job.pk
    plot_output_directory = path.join(get_job_output_folder(job_pk), MEME_PLOT_DIRECTORY)
    if not path.exists(plot_output_directory):
        os.makedirs(plot_output_directory)
    motif_ids = get_motif_ids(job.filtered_meme)
    PlotMeme.plot_meme_list(motif_ids, job.filtered_meme, plot_output_directory)
    # Split one large meme to multiple smaller ones
    split_meme_file(job.filtered_meme, plot_output_directory)
    # Zip motifs
    zip_motifs(motif_ids, plot_output_directory, with_reverse=True)


def plot_bamm_format_generic(job):
    job_pk = str(job.meta_job.job_id)
    src_dir = bamm_directory_old(job_pk) + '/'
    if not os.path.exists(meme_plot_directory(job_pk)):
        os.makedirs(meme_plot_directory(job_pk))
    prefixnames = [os.path.splitext(x)[0] for x in os.listdir(src_dir) if x.endswith(".ihbcp")]
    for prefix in prefixnames:
        cmd = ['plotBaMMLogo.R', src_dir, prefix, PENG_PLOT_LOGO_ORDER, '--web', '1']
        run_command(cmd)
    rename_and_move_plots(src_dir, meme_plot_directory(job_pk))
    motif_ids = get_motif_ids(job.filtered_meme)
    split_meme_file(job.filtered_meme, meme_plot_directory(job_pk))
    ZipMotifs.zip_motifs(motif_ids, meme_plot_directory(job_pk), with_reverse=True)


@task(bind=True)
def peng_seeding_pipeline(self, job_pk):
    job = get_object_or_404(PengJob, meta_job__pk=job_pk)
    job_pk = job.meta_job.pk

    job.meta_job.status = "running"
    job.meta_job.save()

    with JobSaveManager(job):
        make_job_folder(job_pk)

        run_peng_generic(job)
        run_pwm_filter_generic(job)
        job.num_motifs = min(job.num_motifs, job.max_refined_motifs)

        convert_to_bamm_generic(job)
        plot_bamm_format_generic(job)

        job.meta_job.complete = True

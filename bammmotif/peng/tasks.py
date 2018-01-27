from __future__ import absolute_import


from bammmotif.utils import JobSaveManager, make_job_folder, get_log_file
from celery import task, chain
from django.shortcuts import get_object_or_404
from django.conf import settings
from bammmotif.models import Job, PengJob_deprecated, Peng, JobInfo
from bammmotif.peng.settings import (
    FASTA_VALIDATION_SCRIPT,
    MEME_PLOT_INPUT,
    JOB_OUTPUT_DIRECTORY,
    PENG_PLOT_LOGO_ORDER,
    FILTERPWM_OUTPUT_FILE,
)
from bammmotif.utils import get_result_folder
from bammmotif.command_line import PlotMeme, FilterPWM, ShootPengModule
from bammmotif.peng_utils import get_motif_ids
from bammmotif.peng.settings import MEME_PLOT_DIRECTORY
from bammmotif.peng.utils import zip_motifs, rename_and_move_plots, rename_bamms, zip_bamm_motifs
from bammmotif.peng.io import meme_plot_directory, bamm_directory_old, filter_output_file_old, get_job_directory, \
    file_path_peng, get_temporary_job_dir
from bammmotif.utils.meme_reader import split_meme_file
from utils import deprecated
import subprocess
import os
import sys

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

@task(bind=True)
def run_peng_deprecated(self, job_pk):
    peng_job = get_object_or_404(PengJob_deprecated, pk=job_pk)
    with JobSaveManager(peng_job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        temp_dir = get_temporary_job_dir(job_pk)
        os.makedirs(temp_dir)
        peng = ShootPengModule.from_job(peng_job)
        peng.temp_dir = temp_dir
        peng.set_log_file(logfile)
        peng.run()
        # Compress(job_pk)
        peng_job.complete = True
    return 1 if mgr.had_exception else 0

@task(bind=True)
def run_filter_pwm(self, job_pk):
    peng_job = get_object_or_404(Peng, pk=job_pk)
    with JobSaveManager(peng_job) as mgr:
        directory = os.path.join(get_job_directory(peng_job.job_id.job_id), JOB_OUTPUT_DIRECTORY)
        fpwm = FilterPWM.init_with_extra_directory(directory)
        logfile = get_log_file(job_pk)
        fpwm.set_log_file(logfile)
        fpwm.run()
    return 1 if mgr.had_exception else 0

@task(bind=True)
def run_peng(self, job_pk):
    peng_job = get_object_or_404(Peng, pk=str(job_pk))
    with JobSaveManager(peng_job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        peng = ShootPengModule.from_job(peng_job)
        peng.temp_dir = get_temporary_job_dir(job_pk)
        peng.set_log_file(logfile)
        peng.run()
    return 1 if mgr.had_exception else 0

@task(bind=True)
def finish_up_peng(self, job_pk):
    job_info = get_object_or_404(JobInfo, pk=str(job_pk))
    with JobSaveManager(job_info) as mgr:
        job_info.complete = True
    return 1 if mgr.had_exception else 0


@task(bind=True)
def plot_meme_deprecated(self, job_pk):
    result = get_object_or_404(PengJob_deprecated, pk=job_pk)
    meme_result_file_path = file_path_peng(result.job_ID, result.meme_output)
    plot_output_directory = os.path.join(meme_result_file_path.rsplit('/', maxsplit=1)[0], MEME_PLOT_DIRECTORY)
    opath = os.path.join(get_result_folder(result.job_ID), MEME_PLOT_DIRECTORY).split('/', maxsplit=1)[1]
    if not os.path.exists(plot_output_directory):
        os.makedirs(plot_output_directory)
    motif_ids = get_motif_ids(meme_result_file_path)
    meme_plotter = PlotMeme()
    meme_plotter.output_file_format = PlotMeme.defaults['output_file_format']
    PlotMeme.plot_meme_list(motif_ids, meme_result_file_path, plot_output_directory)
    # Split one large meme to multiple smaller ones
    split_meme_file(meme_result_file_path, plot_output_directory)
    # Zip motifs
    zip_motifs(motif_ids, plot_output_directory, with_reverse=True)


@task(bind=True)
def plot_meme_meta(self, job_pk):
    result = get_object_or_404(Peng, pk=job_pk)
    meme_result_file_path = os.path.join(get_job_directory(str(result.job_id)), JOB_OUTPUT_DIRECTORY, MEME_PLOT_INPUT)
    plot_output_directory = os.path.join(meme_result_file_path.rsplit('/', maxsplit=1)[0], MEME_PLOT_DIRECTORY)
    if not os.path.exists(plot_output_directory):
        os.makedirs(plot_output_directory)
    motif_ids = get_motif_ids(meme_result_file_path)
    PlotMeme.plot_meme_list(motif_ids, meme_result_file_path, plot_output_directory)
    # Split one large meme to multiple smaller ones
    split_meme_file(meme_result_file_path, plot_output_directory)
    # Zip motifs
    zip_motifs(motif_ids, plot_output_directory, with_reverse=True)

@task(bind=True)
def convert_to_bamm(self, job_pk):
    job = get_object_or_404(Peng, pk=job_pk)
    # create new directory
    target_dir = bamm_directory_old(job.job_id.job_id)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    input_file = filter_output_file_old(job.job_id.job_id)
    subprocess.run(['pwm2bamm.py', input_file, '-o', target_dir])
    rename_bamms(target_dir, input_file)


@task(bind=True)
def get_logo_command(self, job_pk):
    job = get_object_or_404(Peng, pk=job_pk)
    param = []
    param.append('plotBaMMLogo.R')
    param.append(bamm_directory_old(job.job_id.job_id))
    #if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
    #    param.append(basename(os.path.splitext(job.Motif_InitFile.name)[0]))
    #else:
    #    param.append(basename(os.path.splitext(job.Input_Sequences.name)[0]))
    param.append(os.path.splitext(FILTERPWM_OUTPUT_FILE)[0])
    param.append(PENG_PLOT_LOGO_ORDER)
    param.append('--web 1')
    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command

@task(bind=True)
def plot_bamm_format(self, job_pk):
    job = get_object_or_404(Peng, pk=job_pk)
    src_dir = bamm_directory_old(job.job_id.job_id) + '/' # Not sure, if this is needed, but the other code does it as well.
    if not os.path.exists(meme_plot_directory(str(job.job_id.job_id))):
        os.makedirs(meme_plot_directory(str(job.job_id.job_id)))
    prefixnames = [os.path.splitext(x)[0] for x in os.listdir(src_dir) if x.endswith(".ihbcp")]
    for prefix in prefixnames:
        cmd = ['plotBaMMLogo.R', src_dir, prefix, str(PENG_PLOT_LOGO_ORDER), '--web', '1']
        subprocess.run(cmd)
    rename_and_move_plots(src_dir, meme_plot_directory(str(job.job_id.job_id)))
    meme_result_file_path = os.path.join(get_job_directory(str(job.job_id)), JOB_OUTPUT_DIRECTORY, MEME_PLOT_INPUT)
    motif_ids = get_motif_ids(meme_result_file_path)
    split_meme_file(meme_result_file_path, meme_plot_directory(str(job.job_id.job_id)))
    zip_bamm_motifs(motif_ids, meme_plot_directory(str(job.job_id.job_id)), with_reverse=True)


@task(bind=True)
def peng_chain(self, job_pk):
    #ret = chain(run_peng.si(job_pk) | run_filter_pwm.si(job_pk) | plot_meme_meta.si(job_pk) | finish_up_peng.si(job_pk))()
    ret = chain(run_peng.si(job_pk) |
                run_filter_pwm.si(job_pk) |
                convert_to_bamm.si(job_pk) |
                plot_bamm_format.si(job_pk) |
                finish_up_peng.si(job_pk))()
    return ret

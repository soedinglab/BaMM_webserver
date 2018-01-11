from __future__ import absolute_import


from bammmotif.utils import JobSaveManager, make_job_folder, get_log_file
from celery import task, chain
from django.shortcuts import get_object_or_404
from django.conf import settings
from bammmotif.models import Job, PengJob, PengJobMeta, JobMeta
from bammmotif.command_line import ShootPengModule
from bammmotif.peng.settings import FASTA_VALIDATION_SCRIPT
from bammmotif.peng.job import file_path_peng
from bammmotif.utils import get_result_folder
from bammmotif.command_line import PlotMeme
from bammmotif.peng_utils import get_motif_ids
from bammmotif.peng.settings import MEME_PLOT_DIRECTORY
from bammmotif.peng.utils import zip_motifs
from bammmotif.utils.meme_reader import Meme, split_meme_file

import subprocess
import os
import uuid

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
def run_peng(self, job_pk):
    peng_job = get_object_or_404(PengJob, pk=job_pk)
    with JobSaveManager(peng_job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        peng = ShootPengModule.from_job(peng_job)
        peng.set_log_file(logfile)
        peng.run()
        # Compress(job_pk)
        peng_job.complete = True
    return 1 if mgr.had_exception else 0

@task(bind=True)
def run_peng_meta(self, job_pk):
    #job_info = get_object_or_404(JobMeta, pk=uuid.UUID(str(job_pk)))
    #peng_job = get_object_or_404(PengJobMeta, pk=uuid.UUID(str(job_pk)))
    job_info = get_object_or_404(JobMeta, pk=str(job_pk))
    peng_job = get_object_or_404(PengJobMeta, pk=str(job_pk))
    with JobSaveManager(peng_job) as mgr, JobSaveManager(job_info) as j_mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        peng = ShootPengModule.from_job(peng_job)
        peng.set_log_file(logfile)
        peng.run()
        # Compress(job_pk)
        job_info.complete = True
        job_info.save
    return 1 if mgr.had_exception and j_mgr.had_exception else 0

@task(bind=True)
def plot_meme(self, job_pk):
    result = get_object_or_404(PengJob, pk=job_pk)
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
    #result = get_object_or_404(PengJobMeta, pk=uuid.UUID(str(job_pk)))
    result = get_object_or_404(PengJobMeta, pk=str(job_pk))
    meme_result_file_path = file_path_peng(str(result.job_id), result.meme_output)
    plot_output_directory = os.path.join(meme_result_file_path.rsplit('/', maxsplit=1)[0], MEME_PLOT_DIRECTORY)
    opath = os.path.join(get_result_folder(result.job_id), MEME_PLOT_DIRECTORY).split('/', maxsplit=1)[1]
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
def peng_chain(self, job_pk):
    ret = chain(run_peng_meta.si(job_pk) | plot_meme_meta.si(job_pk))()
    return ret

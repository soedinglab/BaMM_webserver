from contextlib import redirect_stdout, redirect_stderr
from os import path
from shutil import copyfile

from django.shortcuts import get_object_or_404
import celery
from celery import task

from ..utils import (
    JobSaveManager,
    run_command,
    make_job_output_folder,
    make_job_folder,
    get_job_input_folder,
    get_job_output_folder,
    get_log_file,
    get_model_order,
    add_motif_iupac,
)

from ..models import MMcompareJob
from .utils import (
    initialize_motifs_compare,
    make_logos,
    add_motif_motif_matches,
)

from .commands import (
    MMcompare,
    get_compare_iupac_command,
)


def generic_mmcompare_task(job):
    with JobSaveManager(job) as mgr:
        job_pk = job.meta_job.pk
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f), redirect_stderr(f):
                MMcompare(job)
    return 1 if mgr.had_exception else 0


def generic_mmcompare_motif_transfer_task(job):
    job_pk = job.meta_job.pk
    make_job_output_folder(job_pk)

    file_prefix = job.filename_prefix
    init_file = path.join(get_job_input_folder(job_pk), path.basename(job.Motif_InitFile.name))
    _, file_extension = path.splitext(job.Motif_InitFile.name)

    if job.Motif_Init_File_Format == 'PWM':
        init_dest = path.join(get_job_output_folder(job_pk), file_prefix + '.meme')
        copyfile(init_file, init_dest)

    if job.Motif_Init_File_Format == 'BaMM':
        # motif file
        init_dest = path.join(get_job_output_folder(job_pk), file_prefix + file_extension)
        copyfile(init_file, init_dest)

        # motif background
        bg_basename = path.basename(job.bgModel_File.name)
        _, bg_ext = path.splitext(bg_basename)
        bg_file = path.join(get_job_input_folder(job_pk), bg_basename)
        bg_dest = path.join(get_job_output_folder(job_pk), file_prefix + bg_ext)
        copyfile(bg_file, bg_dest)

    job.model_order = get_model_order(job)
    job.save()


def generic_mmcompare_prepare_results(job):
    run_command(get_compare_iupac_command(job))
    initialize_motifs_compare(job)
    add_motif_iupac(job)
    make_logos(job)


def generic_mmcompare_import_matches(job):
    add_motif_motif_matches(job)


@task(bind=True)
def mmcompare_pipeline(self, job_pk):
    job = get_object_or_404(MMcompareJob, meta_job__pk=job_pk)
    make_job_folder(job_pk)
    pipeline = celery.chain([
        mmcompare_motif_transfer_task.si(job_pk),
        mmcompare_task.si(job_pk),
        mmcompare_prepare_results.si(job_pk),
        mmcompare_import_matches.si(job_pk),
    ])
    pipeline()
    job.meta_job.complete = True
    job.save()


@task(bind=True)
def mmcompare_task(self, job_pk):
    job = get_object_or_404(MMcompareJob, meta_job__pk=job_pk)
    return generic_mmcompare_task(job)


@task(bind=True)
def mmcompare_motif_transfer_task(self, job_pk):
    job = get_object_or_404(MMcompareJob, meta_job__pk=job_pk)
    return generic_mmcompare_motif_transfer_task(job)


@task(bind=True)
def mmcompare_prepare_results(self, job_pk):
    job = get_object_or_404(MMcompareJob, meta_job__pk=job_pk)
    return generic_mmcompare_prepare_results(job)


@task(bind=True)
def mmcompare_import_matches(self, job_pk):
    job = get_object_or_404(MMcompareJob, meta_job__pk=job_pk)
    return generic_mmcompare_import_matches(job)

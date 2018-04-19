from contextlib import redirect_stdout, redirect_stderr
from os import path
from shutil import copyfile

from django.shortcuts import get_object_or_404
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

from ..utils.meme_reader import get_motif_ids

from ..models import MMcompareJob
from ..tasks import generic_model_zip_task

from .utils import (
    make_logos,
    add_motif_motif_matches,
)
from .commands import (
    MMcompare,
    get_compare_iupac_command,
)


def generic_mmcompare_task(job):
    with JobSaveManager(job):
        job_pk = job.meta_job.pk
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f), redirect_stderr(f):
                MMcompare(job)


def generic_mmcompare_motif_transfer_task(job):
    job_pk = job.meta_job.pk
    make_job_output_folder(job_pk)

    file_prefix = job.filename_prefix
    init_file = path.join(get_job_input_folder(job_pk), path.basename(job.Motif_InitFile.name))
    _, file_extension = path.splitext(job.Motif_InitFile.name)

    if job.Motif_Init_File_Format == 'MEME':
        init_dest = path.join(get_job_output_folder(job_pk), file_prefix + '.meme')
        copyfile(init_file, init_dest)
        job.num_motifs = len(get_motif_ids(init_dest))

    elif job.Motif_Init_File_Format == 'BaMM':

        # motif file
        init_dest = path.join(get_job_output_folder(job_pk), file_prefix + '_motif_1.ihbcp')
        copyfile(init_file, init_dest)

        # motif background
        bg_basename = path.basename(job.bgModel_File.name)
        bg_file = path.join(get_job_input_folder(job_pk), bg_basename)
        bg_dest = path.join(get_job_output_folder(job_pk), file_prefix + '.hbcp')
        copyfile(bg_file, bg_dest)
    else:
        assert False

    job.model_order = get_model_order(job)
    job.save()


def generic_mmcompare_prepare_results(job):
    make_logos(job)
    run_command(get_compare_iupac_command(job))
    add_motif_iupac(job)


def generic_mmcompare_import_matches(job):
    add_motif_motif_matches(job)


@task(bind=True)
def mmcompare_pipeline(self, job_pk):
    job = get_object_or_404(MMcompareJob, meta_job__pk=job_pk)
    with JobSaveManager(job):
        make_job_folder(job_pk)

        generic_mmcompare_motif_transfer_task(job)
        generic_mmcompare_task(job)
        generic_mmcompare_prepare_results(job)
        generic_mmcompare_import_matches(job)
        generic_model_zip_task(job)
        job.meta_job.complete = True

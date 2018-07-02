from contextlib import redirect_stdout, redirect_stderr

from celery import task
from django.shortcuts import get_object_or_404

from bammmotif.bamm import tasks as bamm_tasks

from ..utils import (
    JobSaveManager,
    make_job_folder,
    get_log_file,
    run_command,
)

from .models import BaMMScanJob
from ..mmcompare.tasks import generic_mmcompare_task, generic_mmcompare_import_matches
from ..tasks import generic_model_zip_task
from .commands import (
    BaMMScan,
    create_bed_files,
    can_create_bed,
    copy_bamm_file_to_output,
    get_meme_to_bamm_command,
)


def generic_bammscan_task(job, first_in_pipeline, is_refined_model):
    job_pk = job.meta_job.pk
    # first define log file for redirecting output information
    logfile = get_log_file(job_pk)
    with open(logfile, 'a') as f:
        with redirect_stdout(f), redirect_stderr(f):
            BaMMScan(job, first_in_pipeline, is_refined_model)
            if can_create_bed(job):
                create_bed_files(job)
                job.has_bedfile = True


@task
def bamm_scan_pipeline(job_pk):
    job = get_object_or_404(BaMMScanJob, meta_job__pk=job_pk)
    with JobSaveManager(job):
        make_job_folder(job_pk)

        if job.Motif_Init_File_Format == 'BaMM':
            copy_bamm_file_to_output(job)
        elif job.Motif_Init_File_Format == 'MEME':
            run_command(get_meme_to_bamm_command(job))

        generic_bammscan_task(job, first_in_pipeline=True, is_refined_model=False)
        if job.FDR:
            bamm_tasks.generic_fdr_task(job, first_in_pipeline=False, is_refined=False)
        if job.MMcompare:
            generic_mmcompare_task(job)
            generic_mmcompare_import_matches(job)

        generic_model_zip_task(job)
        job.meta_job.complete = True

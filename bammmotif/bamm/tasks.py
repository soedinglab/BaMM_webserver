from __future__ import absolute_import

import logging
from contextlib import redirect_stdout, redirect_stderr


from celery import task
from django.shortcuts import get_object_or_404

from ..utils import (
    JobSaveManager,
    get_log_file,
    make_job_folder,
)
from ..commands import Compress
from ..bammscan.tasks import generic_bammscan_task
from ..mmcompare.tasks import generic_mmcompare_task, generic_mmcompare_import_matches

from .commands import (
    BaMM, FDR,
)
from .models import BaMMJob, OneStepBaMMJob

from ..peng.tasks import (
    run_peng_generic,
    convert_to_bamm_generic,
    plot_bamm_format_generic,
)

from ..peng.cmd_modules import PengNoSeedsException


logger = logging.getLogger(__name__)


def generic_compress_task(job):
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f):
                Compress(job)


def generic_bamm_task(job, first_in_pipeline, is_refined):
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f), redirect_stderr(f):
                    BaMM(job, first_in_pipeline, is_refined)


def generic_fdr_task(job, first_in_pipeline, is_refined):
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        # first define log file for redirecting output information
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f), redirect_stderr(f):
                FDR(job, first_in_pipeline, is_refined)


@task(bind=True)
def bamm_refinement_pipeline(self, job_pk):
    job = get_object_or_404(BaMMJob, meta_job__pk=job_pk)
    job_pk = job.meta_job.pk
    with JobSaveManager(job):
        make_job_folder(job_pk)

        generic_bamm_task(job, first_in_pipeline=True, is_refined=False)
        if job.score_Seqset:
            generic_bammscan_task(job, first_in_pipeline=False, is_refined_model=True)
        if job.FDR:
            generic_fdr_task(job, first_in_pipeline=False, is_refined=False)
        if job.MMcompare:
            generic_mmcompare_task(job)
            generic_mmcompare_import_matches(job)
        generic_compress_task(job)
        job.meta_job.complete = True


@task(bind=True)
def denovo_pipeline(self, job_pk):
    job = get_object_or_404(OneStepBaMMJob, meta_job__pk=job_pk)
    job_pk = job.meta_job.pk

    job.meta_job.status = "running"
    job.meta_job.save()

    with JobSaveManager(job):
        make_job_folder(job_pk)

        # seeding part
        try:
            peng_no_seeds = False
            run_peng_generic(job)
        except PengNoSeedsException:
            peng_no_seeds = True

        if not peng_no_seeds:
            job.num_motifs = min(job.num_motifs, job.max_refined_motifs)
            convert_to_bamm_generic(job)
            plot_bamm_format_generic(job)

            # prepare for refinement
            job.bamm_init_file = job.meme_output

            # refinement part
            generic_bamm_task(job, first_in_pipeline=True, is_refined=False)
            job.Motif_Init_File_Format = 'BaMM'
            if job.score_Seqset:
                generic_bammscan_task(job, first_in_pipeline=False, is_refined_model=True)
            if job.FDR:
                generic_fdr_task(job, first_in_pipeline=False, is_refined=True)
            if job.MMcompare:
                generic_mmcompare_task(job)
                generic_mmcompare_import_matches(job)
            generic_compress_task(job)

            job.meta_job.complete = True

    if peng_no_seeds:
        job.meta_job.status = 'No motifs found'
        job.meta_job.save()

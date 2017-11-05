from __future__ import absolute_import
from celery import task
from contextlib import redirect_stdout
from django.shortcuts import get_object_or_404
from .models import (
    Job
)
from .commands import (
    BaMM, BaMMScan, FDR, Peng,
    Compress, MMcompare
)
from .utils import (
    get_log_file, make_job_folder,
    JobSaveManager
)


@task(bind=True)
def run_peng(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    with JobSaveManager(job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        with open(logfile, 'w') as f:
            with redirect_stdout(f):
                
                # run PeNGmotif
                Peng(job_pk, False)

                # run optionals
                if job.EM:
                    BaMM(job_pk, True, False)
                if job.score_Seqset:
                    BaMMScan(job_pk, False, True)
                if job.FDR:
                    FDR(job_pk, False, True)
                if job.MMcompare:
                    MMcompare(job_pk, False, False)
                Compress(job_pk)
                job.complete = True

    return 1 if mgr.had_exception else 0


@task(bind=True)
def run_bamm(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    with JobSaveManager(job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        with open(logfile, 'w') as f:
            with redirect_stdout(f):
                # run BaMMmotif
                BaMM(job_pk, True, False)
                # run optionals
                if job.score_Seqset:
                    BaMMScan(job_pk, False, True)
                if job.FDR:
                    FDR(job_pk, False, True)
                if job.MMcompare:
                    MMcompare(job_pk, False, False)
                Compress(job_pk)
                job.complete = True

    return 1 if mgr.had_exception else 0


@task(bind=True)
def run_bammscan(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    with JobSaveManager(job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        with open(logfile, 'w') as f:
            with redirect_stdout(f):
                # run BaMMscore
                BaMMScan(job_pk, True, False)
                # run optionals
                if job.FDR:
                    FDR(job_pk, False, False)
                if job.MMcompare:
                    MMcompare(job_pk, False, True)
                Compress(job_pk)
                job.complete = True

    return 1 if mgr.had_exception else 0


@task(bind=True)
def run_compare(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    with JobSaveManager(job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        with open(logfile, 'w') as f:
            with redirect_stdout(f):
                # run MMcompare
                MMcompare(job_pk, True, True)
                Compress(job_pk)
                job.complete = True

    return 1 if mgr.had_exception else 0

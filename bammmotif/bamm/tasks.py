from __future__ import absolute_import
from celery import task, chain
from contextlib import redirect_stdout
from django.shortcuts import get_object_or_404
from bammmotif.models import (
    Job
)
from bammmotif.commands import (
    BaMM, BaMMScan, FDR, Peng,
    Compress, MMcompare
)
from bammmotif.utils import (
    get_log_file, make_job_folder,
    JobSaveManager
)


@task(bind=True)
def run_peng(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    with JobSaveManager(job) as mgr:
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        print("logfile: ", logfile)
        with open(logfile, 'w') as f:
            with redirect_stdout(f):
                Peng(job_pk, False)
    return 1 if mgr.had_exception else 0


@task(bind=True)
def finish_up_peng(self, job_pk):
    job = get_log_file(Job, job_pk)
    with JobSaveManager(job) as mgr:
        Compress(job_pk)
        job.complete = True
    return 1 if mgr.had_exception else 0

@task(bind=True)
def bamm_em(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    with JobSaveManager(job) as mgr:
        BaMM(job_pk, True, False)
    return 1 if mgr.had_exception else 0

@task(bind=True)
def bamm_scan(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    with JobSaveManager(job) as mgr:
        BaMMScan(job_pk, False, True)
    return 1 if mgr.had_exception else 0

@task(bind=True)
def bamm_fdr(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    with JobSaveManager(job) as mgr:
        FDR(job_pk, False, True)
    return 1 if mgr.had_exception else 0

@task(bind=True)
def mm_compare(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    with JobSaveManager(job) as mgr:
        MMcompare(job_pk, False, False)
    return 1 if mgr.had_exception else 0

@task(bind=True)
def run_bamm(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    tasks = [run_peng.si(job_pk)]
    if job.EM:
        tasks.append(bamm_em.si(job_pk))
    if job.score_Seqset:
        tasks.append(bamm_scan.si(job_pk))
    if job.FDR:
        tasks.append(bamm_fdr.si(job_pk))
    if job.MMcompare:
        tasks.append(mm_compare.si(job_pk))
    tasks.append(finish_up_peng.si(job_pk))
    chain_ret = chain(*tasks)()
    return chain_ret


@task(bind=True)
def run_peng2(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    with JobSaveManager(job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        print("logfile: ", logfile)
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


#@task(bind=True)
#def run_bamm(self, job_pk):
#    job = get_object_or_404(Job, pk=job_pk)
#    with JobSaveManager(job) as mgr:
#        # first define log file for redirecting output information
#        make_job_folder(job_pk)
#        logfile = get_log_file(job_pk)
#        with open(logfile, 'w') as f:
#            with redirect_stdout(f):
#                # run BaMMmotif
#                BaMM(job_pk, True, False)
#                # run optionals
#                if job.score_Seqset:
#                    BaMMScan(job_pk, False, True)
#                if job.FDR:
#                    FDR(job_pk, False, True)
#                if job.MMcompare:
#                    MMcompare(job_pk, False, False)
#                Compress(job_pk)
#                job.complete = True
#
#    return 1 if mgr.had_exception else 0


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

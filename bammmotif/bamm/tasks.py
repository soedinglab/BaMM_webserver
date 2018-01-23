from __future__ import absolute_import
from celery import task, chain
from contextlib import redirect_stdout
from django.shortcuts import get_object_or_404
from bammmotif.models import (
    Bamm, JobInfo
)
from bammmotif.bamm.commands import (
    BaMM, BaMMScan, FDR, Peng,
    Compress, MMcompare
)
from bammmotif.bamm.utils import (
    get_log_file, make_job_folder,
    JobSaveManager
)
import logging
logger = logging.getLogger(__name__)


# Don't use that yet.
class ChainBuilder:

    def __init__(self, job_pk, initializer, finalizer):
        self._job_pk = job_pk
        self._initializer = initializer
        self._finalizer = finalizer
        self._task_list = []

    @property
    def next(self):
        return None

    @next.setter
    def next(self, _task):
        self._task_list.append(_task.si(self._job_pk))

    def pop(self):
        self._task_list.pop()

    def __enter__(self):
        self._task_list.append(self._initializer.si(self._job_pk))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._task_list.append(self._finalizer.si(self._job_pk))
        ret = chain(*self._task_list)()
        return True


@task(bind=True)
def run_peng(self, job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    with JobSaveManager(job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
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
                    MMcompare(job_pk, False)
                Compress(job_pk)
                job = get_object_or_404(Bamm, pk=job_pk)
                job.job_id.complete = True
                job.save()
    return 1 if mgr.had_exception else 0


@task(bind=True)
def run_bamm(self, job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    with JobSaveManager(job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f):
                # run BaMMmotif
                BaMM(job_pk, True, False)
                # run optionals
                if job.score_Seqset:
                    BaMMScan(job_pk, False, True)
                if job.FDR:
                    FDR(job_pk, False, True)
                if job.MMcompare:
                    MMcompare(job_pk, False)
                Compress(job_pk)
                job = get_object_or_404(Bamm, pk=job_pk)
                job.job_id.complete = True
    job.save()
    return 1 if mgr.had_exception else 0


@task(bind=True)
def run_bammscan(self, job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    with JobSaveManager(job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f):

                # run BaMMscore
                BaMMScan(job_pk, True, False)
                # run optionals
                if job.FDR:
                    FDR(job_pk, False, False)
                if job.MMcompare:
                    MMcompare(job_pk, False)
                Compress(job_pk)
                job = get_object_or_404(Bamm, pk=job_pk)
                job.job_id.complete = True
    job.save()
    return 1 if mgr.had_exception else 0


@task(bind=True)
def run_compare(self, job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    with JobSaveManager(job) as mgr:
        # first define log file for redirecting output information
        make_job_folder(job_pk)
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f):
                # run MMcompare
                MMcompare(job_pk, True)
                Compress(job_pk)
                job = get_object_or_404(Bamm, pk=job_pk)
                job.job_id.complete = True
    job.save()
    return 1 if mgr.had_exception else 0


@task(bind=True)
def prepare_job(self, job_pk):
    make_job_folder(job_pk)
    return 1



@task(bind=True)
def peng(self, job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    with JobSaveManager(job) as mgr:
        # first define log file for redirecting output information
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f):

                # run PeNGmotif
                Peng(job_pk, False)
    return 1 if mgr.had_exception else 0

@task(bind=True)
def bamm(self, job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    with JobSaveManager(job) as mgr:
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f):
                    BaMM(job_pk, True, False)
    return 1 if mgr.had_exception else 0

@task(bind=True)
def bamm_scan(self, job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    with JobSaveManager(job) as mgr:
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f):
                BaMMScan(job_pk, False, True)
    return 1 if mgr.had_exception else 0

@task(bind=True)
def fdr(self, job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    with JobSaveManager(job) as mgr:
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f):
                FDR(job_pk, False, True)
    return 1 if mgr.had_exception else 0

@task(bind=True)
def mmcompare(self, job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    with JobSaveManager(job) as mgr:
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f):
                MMcompare(job_pk, False)
    return 1 if mgr.had_exception else 0


@task(bind=True)
def complete_job(self, job_pk):
    job = get_object_or_404(JobInfo, pk=job_pk)
    with JobSaveManager(job) as mgr:
        logfile = get_log_file(job_pk)
        with open(logfile, 'a') as f:
            with redirect_stdout(f):
                Compress(job_pk)
                job.complete = True
                #job = get_object_or_404(Bamm, pk=job_pk)
                #job.job_id.complete = True
                #job.job_id.save()
    return 1 if mgr.had_exception else 0

@task(bind=True)
def build_and_exec_chain(self, job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    task_list = [prepare_job.si(job_pk)]
    if job.Motif_Initialization == 'PEnGmotif':
        task_list.append(peng.si(job_pk))
        if job.EM:
            task_list.append(bamm.si(job_pk))
    else:
        task_list.append(bamm.si(job_pk))
    if job.score_Seqset:
        task_list.append(bamm_scan.si(job_pk))
    if job.FDR:
        task_list.append(fdr.si(job_pk))
    if job.MMcompare:
        task_list.append(mmcompare.si(job_pk))
    task_list.append(complete_job.si(job_pk))
    ret = chain(*task_list)()
    return ret


@task(bind=True)
def build_and_exec_bammscan_chain(self, job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    task_list = [prepare_job.si(job_pk)]
    if job.FDR:
        task_list.append(fdr.si(job_pk))
    if job.MMcompare:
        task_list.append(mmcompare.si(job_pk))
    task_list.append(complete_job.si(job_pk))
    ret = chain(*task_list)()
    return ret

@task(bind=True)
def build_and_exec_mmcompare_chain(self, job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    task_list = [prepare_job.si(job_pk), mmcompare.si(job_pk), complete_job.si(job_pk)]
    ret = chain(*task_list)()
    return ret

from os import path
import sys

from django.utils import timezone

from ..utils import (
    get_job_output_folder,
    get_model_order,
    run_command,
    meme_count_motifs,
)


def get_MMcompare_command(job):
    job_pk = job.meta_job.pk
    motif_db = job.motif_db
    params = [
        'MMcompare_PWM.R',
        get_job_output_folder(job_pk),
        job.filename_prefix,
        '--dbDir', motif_db.db_model_directory,
        '--dbOrder', motif_db.model_parameters.modelorder,
        '--qOrder', job.model_order,
        '--max_evalue', job.e_value_cutoff,
    ]
    if hasattr(job, 'mmcompare_from_meme'):
        if job.mmcompare_from_meme:
            params.append('--meme-files')
    return params


def MMcompare(job):
    job.meta_job.status = 'running Motif Motif Comparison'
    job.meta_job.save()
    print(timezone.now(), "\t | update: \t %s " % job.meta_job.status)
    sys.stdout.flush()

    if hasattr(job, 'mmcompare_from_meme'):
        if job.mmcompare_from_meme:
            meme_file = job.full_motif_file_path
            job.num_motifs = meme_count_motifs(meme_file)
    run_command(get_MMcompare_command(job))
    job.save()
    sys.stdout.flush()


def get_pwm2bamm_command(job):
    job_pk = job.meta_job.pk
    param = []
    param.append('pwm2bamm.py')
    prefix = job.filename_prefix
    meme_file = path.join(get_job_output_folder(job_pk), prefix + '.meme')
    param.append(meme_file)
    return param


def get_jointprob_command(job):
    job_pk = job.meta_job.pk
    prefix = job.filename_prefix
    params = [
        'getProbfromConProb.R',
        get_job_output_folder(job_pk) + '/',
        prefix
    ]
    return params


def get_compare_iupac_command(job):
    job_pk = job.meta_job.pk
    prefix = job.filename_prefix
    params = [
        'IUPAC.py',
        get_job_output_folder(job_pk) + '/',
        prefix,
        get_model_order(job),
        'BaMM'
    ]
    return params

import glob
from os import path

from django.conf import settings
from django.utils import timezone

from .utils import (
    run_command,
)
from .utils.path_helpers import (
    get_job_output_folder,
)

from logging import getLogger
logger = getLogger(__name__)


def get_logo_command(job, order):
    job_pk = job.meta_job.pk
    prefix = job.filename_prefix
    command = [
        'plotBaMMLogo.R',
        get_job_output_folder(job_pk) + '/',
        prefix,
        order,
        '--web',
        1,
    ]
    return command


def get_distribution_command(job):
    job_pk = job.meta_job.pk
    command = [
        'plotMotifDistribution.R',
        get_job_output_folder(job_pk) + '/',
        job.filename_prefix,
    ]
    return command


def get_iupac_command(job):
    job_pk = job.meta_job.pk
    command = [
        'IUPAC.py',
        get_job_output_folder(job_pk) + '/',
        job.filename_prefix,
        job.model_order,
    ]
    return command


zip_file_globs = [
    '*.hbcp',
    '*.ihbcp',
    '*-logo-order-0.png',
    '*-logo-order-0_revComp.png',
    '*-logo-order-1.png',
    '*-logo-order-2.png',
    '*motifPval.png',
    '*motifRRC.png',
    '*motifRRC.pdf',
    '*dataPval.png',
    '*dataRRC.png',
    '*dataRRC.pdf',
    '*distribution.png',
    '*.occurrence',
    '*.bmscore',
    '*.bed',
]

if settings.ZIP_INCLUDE_ZOOPS_STATS:
    zip_file_globs.append('*.zoops.stats')


def get_compress_command(job):
    job_pk = job.meta_job.pk
    param = ['zip', '-j']
    prefix = job.filename_prefix
    param.append(path.join(get_job_output_folder(job_pk), prefix + '_BaMMmotif.zip'))

    for file_glob in zip_file_globs:
        param.extend(glob.glob(path.join(get_job_output_folder(job_pk), file_glob)))
    return param


def get_motif_compress_command(job, motif):
    job_pk = job.meta_job.pk
    output_folder = get_job_output_folder(job_pk)

    zip_file_name = '%s_Motif_%s.zip' % (job.filename_prefix, motif)
    model_file_glob = '%s_motif_%s' % (job.filename_prefix, motif)

    collected_files = []
    for file_glob in zip_file_globs:
        collected_files.extend(glob.glob(path.join(output_folder, model_file_glob + file_glob)))
    collected_files.extend(glob.glob(path.join(output_folder, '*.hbcp')))
    collected_files.extend(glob.glob(path.join(output_folder, '*.bmscore')))

    params = [
        'zip', '-j',
        path.join(output_folder, zip_file_name),
        *collected_files,
    ]
    return params


def Compress(job):
    job.meta_job.status = 'compressing results'
    job.meta_job.save()
    print(timezone.now(), "\t | update: \t %s " % job.meta_job.status, flush=True)

    run_command(get_compress_command(job))
    for motif_no in range(job.num_motifs):
        run_command(get_motif_compress_command(job, motif_no + 1))

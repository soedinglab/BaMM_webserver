import sys
from glob import glob
from os import path
import logging
import shutil
from billiard import Pool

from django.utils import timezone
from django.conf import settings

from ..bamm.commands import get_core_params
from ..utils.job_helpers import (
        get_model_order,
        get_bg_model_order,
        add_motif_iupac,
)
from ..utils import (
    run_command,
    get_job_output_folder,
    meme_count_motifs,
)
from ..utils.occur2bed import convert_to_bed, is_convertible_to_bed
from ..commands import (
    get_iupac_command,
    get_logo_command,
    get_distribution_command,
)

logger = logging.getLogger(__name__)


def rename_init_files(output_dir, filename_prefix):
    for file in glob(path.join(output_dir, filename_prefix + '*_init_motif_*.ihb*p')):
        new_name = file.replace('_init_motif_', '_motif_')
        logger.debug('renaming: %s -> %s', file, new_name)
        shutil.move(file, new_name)
    for file in glob(path.join(output_dir, filename_prefix + '*_init_motif_*.occurrence')):
        new_name = file.replace('_init_motif_', '_motif_')
        logger.debug('renaming: %s -> %s', file, new_name)
        shutil.move(file, new_name)


def BaMMScan(job, first_task_in_pipeline, is_refined_model):
    job.meta_job.status = 'running BaMMScan'
    job.meta_job.save()
    print(timezone.now(), "\t | update: \t %s " % job.meta_job.status)
    sys.stdout.flush()
    if is_refined_model:
        with Pool(settings.N_PARALLEL_THREADS) as pool:
            for motif_no in range(job.num_motifs):
                command = get_BaMMScan_command(job, first_task_in_pipeline, is_refined_model,
                                               motif_no + 1)
                pool.apply_async(run_command, (command,))
            pool.close()
            pool.join()
    else:
        run_command(get_BaMMScan_command(job, first_task_in_pipeline, is_refined_model))

    if first_task_in_pipeline:
        # required also for uploaded BaMMs, as we need to generate .ihbp files
        rename_init_files(get_job_output_folder(job.meta_job.pk), job.filename_prefix)
    sys.stdout.flush()

    if first_task_in_pipeline:
        # generate motif objects
        run_command(get_iupac_command(job))
        add_motif_iupac(job)

        with Pool(settings.N_PARALLEL_THREADS) as pool:
            for order in range(min(job.model_order+1, 3)):
                pool.apply_async(run_command, (get_logo_command(job, order),))
            pool.close()
            pool.join()

    # plot motif distribution
    run_command(get_distribution_command(job))


def get_BaMMScan_command(job, first_task_in_pipeline, is_refined_model, motif_id=1):

    # these side effects should be avoided
    job.extend = 0

    params = [
        'BaMMScan'
    ]

    # adjust model order if running without BaMMmotif
    if not is_refined_model:
        if job.Motif_Init_File_Format == 'BaMM':
            job.model_order = get_model_order(job)
            job.background_Order = get_bg_model_order(job)
        elif job.Motif_Init_File_Format == 'MEME':
            meme_file = job.full_motif_file_path
            job.num_motifs = meme_count_motifs(meme_file)
            job.model_order = 0
        elif job.Motif_Init_File_Format == 'BindingSites':
            job.model_order = 0

    # get params shared between bammmotif bammscan and fdr
    params.extend(get_core_params(job, is_refined_model, motif_id))

    # add specific params
    params += ['--pvalCutoff', job.score_Cutoff]

    if first_task_in_pipeline:
        params.append("--saveInitialModel")

    params.append("--basename")

    if first_task_in_pipeline and job.Motif_Init_File_Format == 'BaMM':
        prefix = job.filename_prefix
    elif (is_refined_model or job.Motif_Init_File_Format == 'BaMM' or
          job.Motif_Init_File_Format == 'BindingSites'):
        prefix = '%s_motif_%s' % (job.filename_prefix, motif_id)
    else:
        if job.Motif_Init_File_Format == 'MEME':
            prefix = job.filename_prefix
    params.append(prefix)

    job.save()
    return params


def create_bed(occurrence_file, job_id, job_name, motif_id):
    base, ext = path.splitext(occurrence_file)
    bed_file = base + '.bed'
    name = '%s_%s' % (job_id, motif_id)
    description = 'BaMMmotif track for %s, motif %s' % (job_name, motif_id)
    with open(bed_file, 'w') as outfile:
        print('track name=%s description="%s" useScore=1 visibility=2' %
              (name, description), file=outfile)
        convert_to_bed(occurrence_file, outfile)


def create_bed_files(job):
    job_id = job.meta_job.job_id
    with Pool(settings.N_PARALLEL_THREADS) as pool:
        job_output_dir = get_job_output_folder(job_id)
        for motif_no in range(job.num_motifs):
            occ_filename = '%s_motif_%s.occurrence' % (job.filename_prefix, motif_no + 1)
            occurrence_file = path.join(job_output_dir, occ_filename)
            args = (occurrence_file, str(job_id), job.meta_job.job_name, motif_no + 1)
            pool.apply_async(create_bed, args)
        pool.close()
        pool.join()


def can_create_bed(job):
    job_id = job.meta_job.job_id
    job_output_dir = get_job_output_folder(job_id)
    occ_filename = '%s_motif_1.occurrence' % job.filename_prefix
    occurrence_file = path.join(job_output_dir, occ_filename)
    return is_convertible_to_bed(occurrence_file)

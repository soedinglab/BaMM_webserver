import sys
from os import path

from django.utils import timezone

from ..bamm.commands import get_core_params
from ..utils.job_helpers import (
        get_model_order,
        get_bg_model_order,
        add_motif_iupac,
)
from ..utils import (
    run_command,
    get_job_input_folder,
    meme_count_motifs,
)
from ..commands import (
    get_iupac_command,
    get_logo_command,
    get_distribution_command,
)


def BaMMScan(job, first_task_in_pipeline, is_refined_model):
    job.meta_job.status = 'running BaMMScan'
    job.save()
    print(timezone.now(), "\t | update: \t %s " % job.meta_job.status)
    sys.stdout.flush()
    if is_refined_model:
        for motif_no in range(job.num_motifs):
            run_command(get_BaMMScan_command(job, first_task_in_pipeline, is_refined_model,
                                             motif_no+1))
    else:
        run_command(get_BaMMScan_command(job, first_task_in_pipeline, is_refined_model))
    sys.stdout.flush()

    if first_task_in_pipeline:
        # generate motif objects
        run_command(get_iupac_command(job))
        add_motif_iupac(job)
        for order in range(min(job.model_order+1, 3)):
            run_command(get_logo_command(job, order))
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
        elif job.Motif_Init_File_Format == 'PWM':
            meme_file = str(job.Motif_InitFile)
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

    if (is_refined_model or job.Motif_Init_File_Format == 'BaMM' or
       job.Motif_Init_File_Format == 'BindingSites'):
        prefix = '%s_motif_%s' % (job.filename_prefix, motif_id)
    else:
        if job.Motif_Init_File_Format == 'PWM':
            prefix = job.filename_prefix
    params.append(prefix)

    job.save()
    command = ' '.join(str(s) for s in params)
    return command

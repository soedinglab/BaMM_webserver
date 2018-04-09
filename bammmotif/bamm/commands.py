import sys
import os
from os import path
from os.path import basename
import datetime

from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone


from ..models import MotifDatabase
from ..utils import (
    run_command,
    get_job_output_folder,
    get_job_input_folder,
    get_job_folder,
    get_model_order,
    get_bg_model_order,
    add_motif_iupac,

)
from ..commands import (
    get_iupac_command,
    get_logo_command,
)

from ..mmcompare.utils import add_motif_motif_matches
from .models import BaMMJob
from .utils import (
    add_motif_evaluation,
    transfer_motif,
    add_peng_output,
)


def get_core_params(job, is_refined_model, motif_id=1):

    job_pk = job.meta_job.pk

    job_output_folder = get_job_output_folder(job_pk)

    sequence_file = path.join(settings.JOB_DIR, job.Input_Sequences.name)

    params = [
        job_output_folder,
        sequence_file,
    ]

    if str(job.Background_Sequences.name) != '':
        params.append("--negSeqFile")
        params.append(path.join(settings.JOB_DIR, job.Background_Sequences.name))

    if is_refined_model:
        # initialize with refined model

        # careful, this method unfortunately has side effects
        job.Motif_Init_File_Format == "BaMM"
        model_file = '%s_motif_%s.ihbcp' % (job.filename_prefix, motif_id)
        bg_file = '%s.hbcp' % job.filename_prefix
        params += [
            '--BaMMFile', path.join(job_output_folder, model_file),
            '--bgModelFile', path.join(job_output_folder, bg_file),
        ]
    else:
        motif_init_file = job.bamm_init_file
        if str(job.Motif_Init_File_Format) == "BindingSites":
            params += ['--bindingSiteFile', motif_init_file]
        elif str(job.Motif_Init_File_Format) == "MEME":
            params += ['--PWMFile', motif_init_file]
            if hasattr(job, 'max_refined_motifs'):
                params += ['--maxPWM', job.max_refined_motifs]
        elif str(job.Motif_Init_File_Format) == "BaMM":
            assert str(job.bgModel_File) != ''
            params += [
                '--BaMMFile', motif_init_file,
                '--bgModelFile', path.join(settings.JOB_DIR, str(job.bgModel_File))
            ]
        else:
            assert False

    # general options
    if not job.reverse_Complement:
        params.append('--ss')

    params += [
        '--order', job.model_order,
        '--Order', job.background_Order,
    ]

    try:
        params += ['--extend', job.extend, job.extend]
    except AttributeError:
        pass

    return params


def get_evaluation_command(job):
    job_pk = job.meta_job.pk
    command = [
        'evaluateBaMM.R',
        get_job_output_folder(job_pk) + '/',
        job.filename_prefix,
        '--SFC', '1',
        '--ROC5', '1',
        '--PRC', '1',
    ]
    return command


def get_FDR_command(job, useRefined, model_no=1):
    params = ['FDR']
    params += get_core_params(job, useRefined, model_no)
        
    params += [
        '--cvFold 1',  # hard-coded set to 1
        '--mFold', job.m_Fold,
        '--sOrder', job.sampling_Order,
        '--basename',
    ]
    
    if (useRefined or job.Motif_Init_File_Format == 'BaMM'
       or job.Motif_Init_File_Format == 'BindingSites'):
        prefix = '%s_motif_%s' % (job.filename_prefix, model_no)
        params.append(prefix)
    else:
        if job.Motif_Init_File_Format == 'MEME':
            prefix = job.filename_prefix
            params.append(prefix)

    return params


def BaMM(job, first_task_in_pipeline, useRefined):
    job.meta_job.status = 'running BaMMmotif'
    job.meta_job.save()
    print(timezone.now(), "\t | update: \t %s " % job.meta_job.status)
    sys.stdout.flush()
    run_command(get_BaMMmotif_command(job, useRefined, first_task_in_pipeline, 5))
    sys.stdout.flush()
    # add IUPACs
    run_command(get_iupac_command(job))
    add_motif_iupac(job)
    # plot logos
    for order in range(min(job.model_order+1, 3)):
        run_command(get_logo_command(job, order))


def get_BaMMmotif_command(job, useRefined, first, maxPWMs=5):

    command = ['BaMMmotif']
    command.extend(get_core_params(job, useRefined))

    command.append("--EM")
    command.append("-q")
    command.append(job.q_value)
    command.append("--verbose")

    return command


def FDR(job, first_task_in_pipeline, useRefined):
    job.meta_job.status = 'running Motif Evaluation'
    job.save()
    print(timezone.now(), "\t | update: \t %s " % job.meta_job.status)
    sys.stdout.flush()
    if useRefined:
        for m in range(1, job.num_motifs+1):
            run_command(get_FDR_command(job, useRefined, m))
    else:
        run_command(get_FDR_command(job, useRefined))
    sys.stdout.flush()
    # plot motif evaluation
    run_command(get_evaluation_command(job))
    add_motif_evaluation(job)

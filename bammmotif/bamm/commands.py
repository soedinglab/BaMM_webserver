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
)

from .models import BaMMJob
from .utils import (
    add_motif_evaluation,
    add_motif_motif_matches,
    add_motif_iupac,
    transfer_motif,
    add_peng_output,
    initialize_motifs_compare
)


def get_core_params(job, is_refined_model, motif_id=1):

    job_pk = job.meta_job.pk

    job_folder = get_job_folder(job_pk)
    job_output_folder = get_job_output_folder(job_pk)
    sequence_file = path.join(job_folder, job.Input_Sequences.name)

    params = [
        job_output_folder,
        sequence_file,
    ]

    if str(job.Background_Sequences.name) != '':
        params.append("--negSeqFile")
        params.append(path.join(job_folder, job.Background_Sequences.name))

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
        motif_init_file = path.join(job_folder, job.Motif_InitFile.name)
        if str(job.Motif_Init_File_Format) == "BindingSites":
            params += ['--bindingSiteFile', motif_init_file]
        elif str(job.Motif_Init_File_Format) == "PWM":
            params += ['--PWMFile', motif_init_file]
        elif str(job.Motif_Init_File_Format) == "BaMM":
            assert str(job.bgModel_File) != ''
            params += [
                '--BaMMFile', motif_init_file,
                '--bgModelFile', path.join(job_folder, str(job.bgModel_File))
            ]

    # general options
    if not job.reverse_Complement:
        params.append('--ss')

    params += [
        '--order', job.model_order,
        '--Order', job.background_Order,
        '--maxPWM', job.num_init_motifs,
    ]

    try:
        params += ['--extend', job.extend, job.extend]
    except AttributeError:
        pass

    return params


def get_logo_command(job_pk, order):
    job = get_object_or_404(Bamm, pk=job_pk)
    param = []
    param.append('plotBaMMLogo.R')
    param.append(get_job_output_folder(job_pk) + '/')
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        param.append(basename(os.path.splitext(job.Motif_InitFile.name)[0]))
    else:
        param.append(basename(os.path.splitext(job.Input_Sequences.name)[0]))
    param.append(order)
    param.append('--web 1')
    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def get_distribution_command(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    param = []
    param.append('plotMotifDistribution.R')
    param.append(get_job_output_folder(job_pk) + '/')
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        param.append(basename(os.path.splitext(job.Motif_InitFile.name)[0]))
    else:
        param.append(basename(os.path.splitext(job.Input_Sequences.name)[0]))
    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def get_evaluation_command(job):
    job_pk = job.meta_job.pk
    params = [
        'evaluateBaMM.R',
        get_job_output_folder(job_pk) + '/',
        job.filename_prefix,
        '--SFC 1',
        '--ROC5 1',
        '--PRC 1',
    ]
    command = ' '.join(str(s) for s in params)
    return command


def get_iupac_command(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    param = []
    param.append('IUPAC.py')
    param.append(get_job_output_folder(job_pk) + '/')
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        param.append(basename(os.path.splitext(job.Motif_InitFile.name)[0]))
    else:
        param.append(basename(os.path.splitext(job.Input_Sequences.name)[0]))

    if job.job_id.mode == "Compare":
        param.append(get_model_order(job_pk))
        param.append(job.Motif_Init_File_Format)
    else:
        param.append(job.model_Order)
    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def get_prob_command(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    param = []
    param.append('getProbfromConProb.R')
    param.append(get_job_output_folder(job_pk) + '/')
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        param.append(basename(os.path.splitext(job.Motif_InitFile.name)[0]))
    else:
        param.append(basename(os.path.splitext(job.Input_Sequences.name)[0]))
    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def make_logos(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    if job.Motif_Init_File_Format == "PWM":
        run_command(get_convert_input_command(job_pk))
        run_command(get_logo_command(job_pk, 0))
    if job.Motif_Init_File_Format == "BaMM":
        run_command(get_prob_command(job_pk))
        for order in range(min(job.model_Order+1, 3)):
            run_command(get_logo_command(job_pk, order))


def get_convert_input_command(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    param = []
    param.append('pwm2bamm.py')
    infilename = basename(os.path.splitext(job.Motif_InitFile.name)[0])
    infile = get_job_output_folder(job_pk) + '/' + infilename + ".meme"
    param.append(infile)
    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def get_compress_command(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    param = []
    param.append('zip -j')
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        outname = basename(os.path.splitext(job.Motif_InitFile.name)[0])
    else:
        outname = basename(os.path.splitext(job.Input_Sequences.name)[0])
    param.append(get_job_output_folder(job_pk) + '/' + outname + '_BaMMmotif.zip')
    param.append(get_job_output_folder(job_pk) + '/*')

    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def get_motif_compress_command(job_pk, motif):
    job = get_object_or_404(Bamm, pk=job_pk)
    param = []
    param.append('zip -j')
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        outname = basename(os.path.splitext(job.Motif_InitFile.name)[0])
    else:
        outname = basename(os.path.splitext(job.Input_Sequences.name)[0])
    param.append(get_job_output_folder(job_pk) + '/' + outname + '_Motif_' + str(motif) + '.zip')
    param.append(get_job_output_folder(job_pk) + '/' + outname + '_motif_' + str(motif) + '*')
    param.append(get_job_output_folder(job_pk) + '/' + outname + '.hb*')
    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def get_peng_command(job_pk, useRefined):
    job = get_object_or_404(Bamm, pk=job_pk)
    param = []
    param.append("peng_motif")
    param.append(path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))
    param.append("-o")
    param.append(path.join(get_job_input_folder(job_pk), settings.PENG_OUT))
    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def get_FDR_command(job, useRefined, model_no=1):
    job_pk = job.meta_job.pk
    params = ['FDR']
    params += get_core_params(job, useRefined, model_no)
        
    params += [
        '--cvFold 1',  # hard-coded set to 1
        '--mFold', job.m_Fold,
        '--sOrder', job.sampling_Order,
        '--basename',
    ]
    
    output_folder = get_job_output_folder(job_pk)
    if (useRefined or job.Motif_Init_File_Format == 'BaMM'
       or job.Motif_Init_File_Format == 'BindingSites'):
        prefix = '%s_motif_%s' % (job.filename_prefix, model_no)
        params.append(path.join(output_folder, prefix))
    else:
        if job.Motif_Init_File_Format == 'PWM':
            prefix = job.filename_prefix
            params.append(path.join(output_folder, prefix))

    command = ' '.join(str(s) for s in params)
    return command


def get_BaMMScan_command(job_pk, first_task_in_pipeline, useRefined, m=1):
    job = get_object_or_404(Bamm, pk=job_pk)
    param = []

    # define executable
    param.append('BaMMScan')

    # adjust extensions
    job.extend = 0
    job.save()

    # adjust model order if run without BaMMmotif
    if not useRefined and job.Motif_Init_File_Format == 'BaMM':
        job.model_Order = get_model_order(job_pk)
        job.background_Order = get_bg_model_order(job_pk)
        job.save()

    if not useRefined and (job.Motif_Init_File_Format == 'PWM' or job.Motif_Init_File_Format == 'BindingSites'):
        job.model_Order = 0
        job.save()

    # get params shared between bammmotif bammscan and fdr
    param.append(get_core_params(job_pk, useRefined, m))

    # add specific params
    param.append("--pvalCutoff")
    param.append(job.score_Cutoff)

    if first_task_in_pipeline:
        param.append("--saveInitialModel")

    param.append("--basename")
    if useRefined or job.Motif_Init_File_Format == 'BaMM' or job.Motif_Init_File_Format == 'BindingSites':
        param.append(str(job.Output_filename()) + '_motif_' + str(m))
    else:
        if job.Motif_Init_File_Format == 'PWM':
            param.append(job.Output_filename())

    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def get_BaMMmotif_command(job_pk, useRefined, first, maxPWMs=5):
    job = get_object_or_404(Bamm, pk=job_pk)
    param = []

    # restrict to top 5 motifs from PeNG
    if job.Motif_Initialization == "PEnGmotif":
        job.num_init_motifs = maxPWMs
        job.save()

    # define executable
    param.append('BaMMmotif')

    # get params shared between bammmotif bammscan and fdr
    param.append(get_core_params(job_pk, useRefined))

    # add specific params
    param.append("--EM")
    param.append("-q")
    param.append(job.q_value)
    param.append("--verbose")

    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def get_MMcompare_command(job_pk, db_id):
    job = get_object_or_404(Bamm, pk=job_pk)
    motif_db = get_object_or_404(MotifDatabase, pk=db_id)

    param = []
    param.append('MMcompare_PWM.R')
    param.append(get_job_output_folder(job_pk))
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        param.append(basename(os.path.splitext(job.Motif_InitFile.name)[0]))
    else:
        param.append(basename(os.path.splitext(job.Input_Sequences.name)[0]))
    param.append('--dbDir')
    param.append(path.join(settings.MOTIF_DATABASE_PATH, motif_db.db_id, 'models'))
    param.append('--dbOrder')
    param.append(motif_db.model_parameters.modelorder)
    param.append('--qOrder')
    param.append(job.model_Order)

    param.append('--pValue')
    param.append(job.p_value_cutoff)

    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def Peng(job_pk, useRefined):
    job = get_object_or_404(Bamm, pk=job_pk)
    job.status = 'running PEnGmotif'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    run_command(get_peng_command(job_pk, useRefined))
    sys.stdout.flush()
    # add output to the input for further optionals
    add_peng_output(job_pk)
    return 0


def BaMM(job_pk, first_task_in_pipeline, useRefined):
    job = get_object_or_404(Bamm, pk=job_pk)
    job.status = 'running BaMMmotif'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    sys.stdout.flush()
    run_command(get_BaMMmotif_command(job_pk, useRefined, first_task_in_pipeline, 5))
    sys.stdout.flush()
    if first_task_in_pipeline:
        # generate motif objects
        initialize_motifs(job_pk, 2, 2)
        job = get_object_or_404(Bamm, pk=job_pk)
    # add IUPACs
    run_command(get_iupac_command(job_pk))
    add_motif_iupac(job_pk)
    # plot logos
    for order in range(min(job.model_Order+1, 3)):
        run_command(get_logo_command(job_pk, order))
    return 0


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


def Compress(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    job.status = 'compressing results'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    sys.stdout.flush()
    run_command(get_compress_command(job_pk))
    for motif in range(1, (int(job.num_motifs) + 1)):
        run_command(get_motif_compress_command(job_pk, motif))
    return 0

import glob
import sys
import os
from os import path
from os.path import basename
import datetime

from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone

from .models import (
    DbParameter
)
from .utils import (
    run_command, initialize_motifs,
    add_motif_evaluation,
    add_motif_iupac,
    transfer_motif,
    add_peng_output,
    get_model_order,
    get_bg_model_order,
    initialize_motifs_compare
)
from .utils.path_helpers import (
    get_job_output_folder,
    get_job_input_folder,
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


def get_evaluation_command(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    param = []
    param.append('evaluateBaMM.R')
    param.append(get_job_output_folder(job_pk) + '/')
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        param.append(basename(os.path.splitext(job.Motif_InitFile.name)[0]))
    else:
        param.append(basename(os.path.splitext(job.Input_Sequences.name)[0]))
    param.append('--SFC 1')
    param.append('--ROC5 1')
    param.append('--PRC 1')
    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
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


def get_prob_command(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
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
    job = get_object_or_404(Job, pk=job_pk)
    if job.Motif_Init_File_Format == "PWM":
        run_command(get_convert_input_command(job_pk))
        run_command(get_logo_command(job_pk, 0))
    if job.Motif_Init_File_Format == "BaMM":
        run_command(get_prob_command(job_pk))
        for order in range(min(job.model_Order+1, 3)):
            run_command(get_logo_command(job_pk, order))


def get_convert_input_command(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    param = []
    param.append('pwm2bamm.py')
    infilename = basename(os.path.splitext(job.Motif_InitFile.name)[0])
    infile = get_job_output_folder(job_pk) + '/' + infilename + ".meme"
    param.append(infile)
    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
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
]


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

    params = [
        'zip', '-j',
        path.join(output_folder, zip_file_name),
        *collected_files,
    ]
    return params


def get_peng_command(job_pk, useRefined):
    job = get_object_or_404(Job, pk=job_pk)
    param = []
    param.append("peng_motif")
    param.append(path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))
    param.append("-o")
    param.append(path.join(get_job_input_folder(job_pk), settings.PENG_OUT))
    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def get_FDR_command(job_pk, useRefined, m=1):
    # set cvFold to 1
    job = get_object_or_404(Job, pk=job_pk)
    param = []

    # define executable
    param.append('FDR')

    # get params shared between bammmotif bammscan and fdr
    param.append(get_core_params(job_pk, useRefined, m))

    # add specific params
    param.append("--cvFold 1")
    param.append("--mFold")
    param.append(job.m_Fold)
    param.append("--sOrder")
    param.append(job.sampling_Order)

    param.append("--basename")
    if useRefined is True or job.Motif_Init_File_Format == 'BaMM'or job.Motif_Init_File_Format == 'BindingSites':
        param.append(str(job.Output_filename()) + '_motif_' + str(m))
    else:
        if job.Motif_Init_File_Format == 'PWM':
            param.append(job.Output_filename())

    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def get_BaMMScan_command(job_pk, first, useRefined, m=1):
    job = get_object_or_404(Job, pk=job_pk)
    param = []

    # define executable
    param.append('BaMMScan')

    # adjust extensions
    job.extend = 0
    job.save()

    # adjust model order if run without BaMMmotif
    if useRefined is False and job.Motif_Init_File_Format == 'BaMM':
        job.model_Order = get_model_order(job_pk)
        job.background_Order = get_bg_model_order(job_pk)
        job.save()

    if useRefined is False and (job.Motif_Init_File_Format == 'PWM' or job.Motif_Init_File_Format == 'BindingSites'):
        job.model_Order = 0
        job.save()

    # get params shared between bammmotif bammscan and fdr
    param.append(get_core_params(job_pk, useRefined, m))

    # add specific params
    param.append("--pvalCutoff")
    param.append(job.score_Cutoff)

    if first is True:
        param.append("--saveInitialModel")

    param.append("--basename")
    if useRefined is True or job.Motif_Init_File_Format == 'BaMM' or job.Motif_Init_File_Format == 'BindingSites':
        param.append(str(job.Output_filename()) + '_motif_' + str(m))
    else:
        if job.Motif_Init_File_Format == 'PWM':
            param.append(job.Output_filename())

    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def get_BaMMmotif_command(job_pk, useRefined, first, maxPWMs=5):
    job = get_object_or_404(Job, pk=job_pk)
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


def get_MMcompare_command(job_pk, database):
    db = get_object_or_404(DbParameter, pk=database)
    job = get_object_or_404(Job, pk=job_pk)
    param = []

    param.append('MMcompare_PWM.R')
    param.append(get_job_output_folder(job_pk))
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        param.append(basename(os.path.splitext(job.Motif_InitFile.name)[0]))
    else:
        param.append(basename(os.path.splitext(job.Input_Sequences.name)[0]))
    param.append('--dbDir')
    param.append(path.join(settings.BASE_DIR + settings.DB_ROOT + '/' + db.base_dir + '/Results/'))
    param.append('--dbOrder')
    param.append(db.modelorder)
    param.append('--qOrder')
    param.append(job.model_Order)

    param.append('--pValue')
    param.append(job.p_value_cutoff)

    command = " ".join(str(s) for s in param)
    print(command)
    sys.stdout.flush()
    return command


def Peng(job_pk, useRefined):
    job = get_object_or_404(Job, pk=job_pk)
    job.status = 'running PEnGmotif'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    run_command(get_peng_command(job_pk, useRefined))
    sys.stdout.flush()
    # add output to the input for further optionals
    add_peng_output(job_pk)
    return 0


def BaMM(job_pk, first, useRefined):
    job = get_object_or_404(Job, pk=job_pk)
    job.status = 'running BaMMmotif'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    sys.stdout.flush()
    run_command(get_BaMMmotif_command(job_pk, useRefined, first, 5))
    sys.stdout.flush()
    if first:
        # generate motif objects
        initialize_motifs(job_pk, 2, 2)
        job = get_object_or_404(Job, pk=job_pk)

    # add IUPACs
    run_command(get_iupac_command(job_pk))

    add_motif_iupac(job_pk)
    # plot logos
    for order in range(min(job.model_Order+1, 3)):
        run_command(get_logo_command(job_pk, order))
    return 0


def BaMMScan(job_pk, first, useRefined):
    job = get_object_or_404(Job, pk=job_pk)
    job.status = 'running BaMMScan'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    sys.stdout.flush()
    if useRefined is True:
        for m in range(1, job.num_motifs+1):
            run_command(get_BaMMScan_command(job_pk, first, useRefined, m))
    else:
        run_command(get_BaMMScan_command(job_pk, first, useRefined))
    sys.stdout.flush()
    if first is True:
        # generate motif objects
        initialize_motifs(job_pk, 2, 3)
        job = get_object_or_404(Job, pk=job_pk)
        run_command(get_iupac_command(job_pk))
        add_motif_iupac(job_pk)
        # plot logos
        job = get_object_or_404(Job, pk=job_pk)
        for order in range(min(job.model_Order+1, 3)):
            run_command(get_logo_command(job_pk, order))
    # plot motif distribution
    run_command(get_distribution_command(job_pk))
    return 0


def FDR(job_pk, first, useRefined):
    job = get_object_or_404(Job, pk=job_pk)
    job.status = 'running Motif Evaluation'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    sys.stdout.flush()
    if useRefined is True:
        for m in range(1, job.num_motifs+1):
            run_command(get_FDR_command(job_pk, useRefined, m))
    else:
        run_command(get_FDR_command(job_pk, useRefined))
    sys.stdout.flush()
    if first is True:
        # generate motif objects
        initialize_motifs(job_pk, 0, 1)
        job = get_object_or_404(Job, pk=job_pk)
    # plot motif evaluation
    run_command(get_evaluation_command(job_pk))
    add_motif_evaluation(job_pk)
    return 0


def Compress(job):
    job.meta_job.status = 'compressing results'
    job.meta_job.save()
    print(timezone.now(), "\t | update: \t %s " % job.meta_job.status)
    sys.stdout.flush()

    run_command(get_compress_command(job))
    for motif_no in range(job.num_motifs):
        run_command(get_motif_compress_command(job, motif_no + 1))

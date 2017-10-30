from django.shortcuts import get_object_or_404
from django.conf import settings
import sys
import os
from os import path
from os.path import basename
import datetime
from .models import (
    Job, DbParameter
)
from .utils import (
    get_job_output_folder,
    run_command, initialize_motifs,
    add_motif_evaluation,
    add_motif_motif_matches,
    transfer_motif
)


def get_core_params(job_pk, useRefined, m=1):
    job = get_object_or_404(Job, pk=job_pk)
    root = settings.MEDIA_ROOT
    param = []
    # outputfolder
    param.append(get_job_output_folder(job_pk))
    # sequence file
    param.append(path.join(root, job.Input_Sequences.name))
    if str(job.Background_Sequences.name) != '':
        param.append("--negSeqFile")
        param.append(path.join(root, job.Background_Sequences.name))

    if useRefined is True:
        # Initialize with refined Model
        job.Motif_Init_File_Format == "BaMM"
        job.save()
        param.append("--BaMMFile")
        param.append(get_job_output_folder(job_pk) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(m) + '.ihbcp')
        param.append("--bgModelFile")
        param.append(get_job_output_folder(job_pk) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '.hbcp')
    else:
        # motif Initialization File
        if str(job.Motif_Init_File_Format) == "BindingSite":
            param.append("--BindingSiteFile")
            param.append(path.join(root, job.Motif_InitFile.name))
        if str(job.Motif_Init_File_Format) == "PWM":
            param.append("--PWMFile")
            param.append(path.join(root, job.Motif_InitFile.name))
        if str(job.Motif_Init_File_Format) == "BaMM":
            param.append("--BaMMFile")
            param.append(path.join(root, job.Motif_InitFile.name))
            # when providing a BaMM file, bg File is needed
            if str(job.bgModel_File) == '':
                print('InvalidCommandException')
                # raise InvalidCommandException
            else:
                param.append("--bgModelFile")
                param.append(path.join(root, job.bgModel_File.name))

    # general options
    if job.reverse_Complement is False:
        param.append("--ss")
    param.append("--order")
    param.append(job.model_Order)
    param.append("--Order")
    param.append(job.background_Order)
    param.append("--extend")
    param.append(job.extend_1)
    param.append(job.extend_2)
    param.append("--maxPWM")
    param.append(job.num_init_motifs)

    command = " ".join(str(s) for s in param)
    return command


def get_logo_command(job_pk, order):
    job = get_object_or_404(Job, pk=job_pk)
    param = []
    param.append('plotBaMMLogo.R')
    param.append(get_job_output_folder(job_pk) + '/')
    param.append(basename(os.path.splitext(job.Input_Sequences.name)[0]))
    param.append(order)
    param.append('--web 1')
    command = " ".join(str(s) for s in param)
    return command


def get_distribution_command(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    param = []
    param.append('plotMotifDistribution.R')
    param.append(get_job_output_folder(job_pk) + '/')
    param.append(basename(os.path.splitext(job.Input_Sequences.name)[0]))
    command = " ".join(str(s) for s in param)
    return command


def get_evaluation_command(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    param = []
    param.append('evaluateBaMM.R')
    param.append(get_job_output_folder(job_pk) + '/')
    param.append(basename(os.path.splitext(job.Input_Sequences.name)[0]))
    param.append('--SFC 1')
    param.append('--ROC5 1')
    param.append('--PRC 1')
    command = " ".join(str(s) for s in param)
    return command


def get_compress_command(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    param = []
    param.append('zip -j')
    param.append(get_job_output_folder(job_pk) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_BaMMmotif.zip')
    param.append(get_job_output_folder(job_pk) + '/*')
    command = " ".join(str(s) for s in param)
    print(command)
    return command


def get_motif_compress_command(job_pk, motif):
    job = get_object_or_404(Job, pk=job_pk)
    param = []
    param.append('zip -j')
    param.append(get_job_output_folder(job_pk) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_Motif_' + str(motif) + '.zip')
    param.append(get_job_output_folder(job_pk) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif) + '*')
    param.append(get_job_output_folder(job_pk) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '.hb*')
    command = " ".join(str(s) for s in param)
    print(command)
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

    command = " ".join(str(s) for s in param)
    print(command)
    return command


def get_BaMMScan_command(job_pk, useRefined, m=1):
    job = get_object_or_404(Job, pk=job_pk)
    param = []

    # define executable
    param.append('BaMMScan')

    # adjust extensions
    job.extend_1 = 0
    job.extend_2 = 0
    job.save()

    # get params shared between bammmotif bammscan and fdr
    param.append(get_core_params(job_pk, useRefined, m))

    # add specific params
    param.append("--pvalCutoff")
    param.append(job.score_Cutoff)

    command = " ".join(str(s) for s in param)
    print(command)
    return command


def get_BaMMmotif_command(job_pk, useRefined):
    job = get_object_or_404(Job, pk=job_pk)
    param = []

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
    return command


def get_MMcompare_command(job_pk, database):
    db = get_object_or_404(DbParameter, pk=database)
    job = get_object_or_404(Job, pk=job_pk)
    param = []

    param.append('MMcompare_PWM.R')
    param.append(get_job_output_folder(job_pk))
    param.append(basename(os.path.splitext(job.Input_Sequences.name)[0]))
    param.append('--dbDir')
    param.append(path.join(settings.DB_ROOT, db.base_dir, 'Results'))
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


def BaMM(job_pk, first, useRefined):
    job = get_object_or_404(Job, pk=job_pk)
    job.status = 'running BaMMmotif'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    sys.stdout.flush()
    run_command(get_BaMMmotif_command(job_pk, useRefined))
    if first is True:
        # generate motif objects
        initialize_motifs(job_pk, 2, 2)
    # plot logos
    for order in range(min(job.model_Order+1, 4)):
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
            run_command(get_BaMMScan_command(job_pk, useRefined, m))
    else:
        run_command(get_BaMMScan_command(job_pk, useRefined))
    if first is True:
        # generate motif objects
        initialize_motifs(job_pk, 0, 1)
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
    if first is True:
        # generate motif objects
        initialize_motifs(job_pk, 0, 1)
    # plot motif evaluation
    run_command(get_evaluation_command(job_pk))
    add_motif_evaluation(job_pk)
    return 0


def MMcompare(job_pk, first, opt):
    job = get_object_or_404(Job, pk=job_pk)
    job.status = 'running Motif Motif Comparison'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    sys.stdout.flush()
    database = 100
    if opt is True:
        # add init Motif to Outputfolder
        offs = transfer_motif(job_pk)
    run_command(get_MMcompare_command(job_pk, database))
    if first is True:
        # generate motif objects
        initialize_motifs(job_pk, offs, 1)
    add_motif_motif_matches(job_pk)
    return 0


def Compress(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    job.status = 'compressing results'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    sys.stdout.flush()
    run_command(get_compress_command(job_pk))
    for motif in range(1, (int(job.num_motifs) + 1)):
        run_command(get_motif_compress_command(job_pk, motif))
    return 0

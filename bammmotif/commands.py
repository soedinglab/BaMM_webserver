from django.shortcuts import get_object_or_404
from django.conf import settings
from os import path
import datetime
from .models import Job
from .utils import (
    get_job_output_folder,
    run_command
)


def get_core_params(job_pk):
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

def get_logo_command(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    #file_prefix = 
    #basic_name = opath + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif)
    #for order in range(min(job.model_Order+1,4)): 
    #    if order == 0:
    #            
    #            # plot reverse Complement as Stamp version
    #            command = 'plotBaMMLogo.R ' + basic_name + '.ihbcp ' + str(order) + ' --revComp 1 --stamp 1'
                


def get_FDR_command(job_pk):
    # set cvFold to 1
    job = get_object_or_404(Job, pk=job_pk)
    param = []

    # define executable
    param.append('FDR')
    # ### Attention! this would score the INPUT files
    # this is fine for having only run BammScan but not
    # if BaMM motif ran first!

    # get params shared between bammmotif bammscan and fdr
    param.append(get_core_params(job_pk))

    # add specific params
    param.append("--cvFold 1")
    param.append("--mFold")
    param.append(job.m_Fold)
    param.append("--sOrder")
    param.append(job.sampling_Order)

    command = " ".join(str(s) for s in param)
    print(command)
    return command


def get_BaMMScan_command(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    param = []

    # define executable
    param.append('BaMMScan')
    # ### Attention! this would score the INPUT files
    # this is fine for having only run BammScan but not
    # if BaMM motif ran first!

    # get params shared between bammmotif bammscan and fdr
    param.append(get_core_params(job_pk))

    # add specific params
    param.append("--pvalCutoff")
    param.append(job.score_Cutoff)

    command = " ".join(str(s) for s in param)
    print(command)
    return command


def get_BaMMmotif_command(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    param = []

    # define executable
    param.append('BaMMmotif')

    # get params shared between bammmotif bammscan and fdr
    param.append(get_core_params(job_pk))

    # add specific params
    param.append("--EM")
    param.append("-q")
    param.append(job.q_value)
    param.append("--verbose")

    command = " ".join(str(s) for s in param)
    print(command)
    return command


def BaMM(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    job.status = 'running BaMMmotif'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    run_command(get_BaMMmotif_command(job_pk))
    # plot logos
    run_command(get_logo_command(job_pk))
    return 0


def BaMMScan(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    job.status = 'running BaMMScan'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    run_command(get_BaMMScan_command(job_pk))
    return 0


def FDR(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    job.status = 'running Motif Evaluation'
    job.save()
    print(datetime.datetime.now(), "\t | update: \t %s " % job.status)
    run_command(get_FDR_command(job_pk))
    return 0

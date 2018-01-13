from __future__ import absolute_import
import os


from celery import Celery
from celery import shared_task, task
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.files import File
from django.core.mail import send_mail
from django.contrib.auth.models import User
from ipware.ip import get_ip
from .models import *

from os.path import basename
from contextlib import redirect_stdout
import tempfile
import subprocess
import datetime
import os
import sys
import shutil

@task(bind=True)
def valid_init(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    try:
        job.status = 'Check Input File'
        job.save()
        check = subprocess.Popen(['/code/bammmotif/static/scripts/valid_Init',
                                  str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name)),
                                  str(os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)),
                                  str(job.Motif_Init_File_Format) ],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check.wait()
        out, err = check.communicate()
        out = out.decode('ascii')
        if out == "OK":
            return 0
        else:
            return 1

    except Exception as e:
        job.status = 'error'
        job.save()
        return 1

@task(bind=True)
def valid_fasta(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    try:
        job.status = 'Check Input File'
        job.save()
        check = subprocess.Popen(['/code/bammmotif/static/scripts/valid_fasta',
                                  str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check.wait()

        out, err = check.communicate()
        out = out.decode('ascii')
        if out == "OK":
            return 0
        else:
            return 1

    except Exception as e:
        job.status = 'error'
        job.save()
        return 1


@task(bind=True)
def run_peng(self, job_pk):
    # Move command building to somewhere else. Preferrably to create job!
    pass

@task(bind=True)
def run_bamm(self, job_pk):
    """
    Procedure:
    1. Build job.
    2. Execute job.
    3. Processing during job.
    4. Print fdr and position plots plus zipping.
    5. Print logo plots plus zipping.
    6. Create summary file.
    7. Zipping complete job.
    :param self:
    :param job_pk:
    :return:
    """
    job = get_object_or_404(Job, pk=job_pk)
    # first define log file for redirecting output information
    logfile =  str(settings.MEDIA_ROOT) + "/logs/" + str(job_pk) + ".log"
    with open(logfile, 'w') as f:
        with redirect_stdout(f):
            try:
                # run PEnGmotif in case it is selected
                if job.Motif_Initialization == "PEnGmotif":
                    job.status = 'Running PEnGmotif'
                    job.save()
                    print(datetime.datetime.now(), "\t | START: \t %s " % job.status )

                    #command = '/code/bammmotif/static/scripts/peng_motif ' + os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name) + ' -o ' + os.path.join(settings.MEDIA_ROOT, job_pk, 'Input') + '/MotifInitFile.peng'
                    command = 'shoot_peng.py ' + os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name) + ' -o ' + os.path.join(settings.MEDIA_ROOT, job_pk, 'Input') + '/MotifInitFile.peng' +  ' -w 10 --pseudo-counts 10 -b 0.3 -a 1E3'
                    print( "\n %s \n" % command )
                    sys.stdout.flush()
                    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    while True:
                        nextline = process.stdout.readline()
                        if nextline == b'' and process.poll() is not None:
                            break
                        sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                        sys.stdout.flush()
                    process.wait()

                    f = open(str(os.path.join(settings.MEDIA_ROOT, str(job.pk),'Input/', 'MotifInitFile.peng')))
                    job.Motif_InitFile.save("MotifInitFile.peng", File(f))
                    job.Motif_Init_File_Format = "PWM"
                    job.status = "PEnGmotif finished"
                    job.save()
                    print(datetime.datetime.now(), "\t | update: \t %s " % job.status )
                    sys.stdout.flush()

                file_counter = 4
                # prepare arguments for bamm call
                job.status = "Preparing for BaMM!motif"
                job.save()
                if job.Motif_Initialization == "PEnGmotif":
                    print(datetime.datetime.now(), "\t | update: \t %s " % job.status )
                else:
                    print(datetime.datetime.now(), "\t | START: \t %s " % job.status )

                opath = os.path.join(settings.MEDIA_ROOT, str(job_pk),"Output")
                params = opath + " " + str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))

                # optional Files
                if job.Background_Sequences.name != '':
                    params = params + " --negSeqFile " +  os.path.join(settings.MEDIA_ROOT, job.Background_Sequences.name)
                if job.Intensity_File.name != '':
                    params = params + " --intensityFile " + os.path.join(settings.MEDIA_ROOT, job.Intensity_File.name)

                # motif Initialization File
                if str(job.Motif_Init_File_Format) == "BindingSites":
                    params = params + " --bindingSiteFile " + os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)
                if str(job.Motif_Init_File_Format) == "PWM":
                    params = params + " --PWMFile " + os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)
                    #params = params + " --num " + str(job.num_init_motifs)
                    #params = params + " --num 1"
                if str(job.Motif_Init_File_Format) == "BaMM":
                    params = params + " --BaMMFile " + os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)

                    if str(job.mode) == "Occurrence":
                        # find out model Order of init file if not given
                        command = 'python3 /code/bammmotif/static/scripts/getModelOrder.py ' + os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)
                        print(command)
                        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        # Poll process for new output until finished
                        #TODO: Why not use process.stdout.readlines()
                        while True:
                            nextline = process.stdout.readline()
                            if nextline == b'' and process.poll() is not None:
                                break
                            sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                            job.model_Order = int(nextline.strip().decode('ascii'))
                            job.save()
                            print("Model order = " + str(job.model_Order)+ "\n")
                            sys.stdout.flush()
                        process.wait()

                        # add bgModelFile as parameter and find out bgModel order
                        params = params + " --bgFile " + os.path.join(settings.MEDIA_ROOT, job.bgModel_File.name)
                        command = 'python3 /code/bammmotif/static/scripts/getbgModelOrder.py ' + os.path.join(settings.MEDIA_ROOT, job.bgModel_File.name)
                        print(command)
                        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        # Poll process for new output until finished
                        while True:
                            nextline = process.stdout.readline()
                            if nextline == b'' and process.poll() is not None:
                                break
                            sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                            job.background_Order = int(nextline.strip().decode('ascii'))
                            job.save()
                            print("BG order = " + str(job.background_Order)+ "\n")
                            sys.stdout.flush()
                        process.wait()

                # general options
                params = params +  " --order " + str(job.model_Order)
                if job.reverse_Complement == False:
                    params = params +  " --ss "
                params = params + " --extend " + str(job.extend_1) +  " " +  str(job.extend_2)
                params = params + " --alphabet " + str(job.alphabet)
                params = params + " --Order " +  str(job.background_Order)

                # fdr related options
                if job.FDR == True:
                    params = params + " --FDR "
                    params = params + " --savePRs "
                    params = params + " --zoops "

                    file_counter = file_counter + 1
                    params = params + " --mFold " + str(job.m_Fold)
                    params = params + " --cvFold " + str(job.cv_Fold)
                    params = params + " --samplingOrder " + str(job.sampling_Order)

                # EM related options:
                if job.EM == True:
                    params = params + " --EM "
                    params = params + " --epsilon " + str(job.epsilon)
                    params = params + " --maxEMIterations " + str(job.max_EM_Iterations)

                # Output related options:
                if job.verbose == True:
                    params = params + " --verbose "
                if job.save_LogOdds == True:
                    params = params + " --saveLogOdds "
                    file_counter = file_counter + 1
                if job.save_BaMMs == True:
                    params = params + " --saveBaMMs "
                if job.save_BgModel == True:
                    params = params + " --saveBgModel "
                if job.score_Seqset == True:
                    params = params + " --bammSearch "
                    params = params + " --scoreCutoff " + str(job.score_Cutoff)

                job.status = 'Running BaMM'
                job.save()
                print(datetime.datetime.now(), "\t | update: \t %s " % job.status )

                command = 'BaMMmotif ' + params
                print( "\n %s \n" % command )
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                # Poll process for new output until finished
                while True:
                    nextline = process.stdout.readline()
                    if nextline == b'' and process.poll() is not None:
                        break
                    sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                    sys.stdout.flush()
                process.wait()

                # count how many motifs have been processed ( 2 files come from backgroundModel )
                if job.mode == 'Predicition':
                    job.num_motifs  = (len(os.listdir(opath))-2)/file_counter
                if job.mode == 'Occurrence':
                    job.num_motifs  = (len(os.listdir(opath))-2)/3

                for motif in range(1, (int(job.num_motifs)+1)):

                    job.status = 'Processing motif #%s ...' % motif
                    job.save()
                    print(datetime.datetime.now(), "\t | update: \t %s " % job.status )

                    # generate new motif database entry for current motif
                    motif_obj = Motifs( parent_job = job, job_rank = motif)
                    motif_obj.save()

                    job.status = 'IUPAC for motif #%s ...' % motif
                    job.save()
                    print(datetime.datetime.now(), "\t | update: \t %s " % job.status )

                    # calculate iupac
                    command = 'python3 /code/bammmotif/static/scripts/pwm2iupac.py ' + opath + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif) + '.ihbcp ' + str(job.model_Order)
                    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                    # Poll process for new output until finished
                    while True:
                        nextline = process.stdout.readline()
                        if nextline == b'' and process.poll() is not None:
                            break
                        sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                        motif_obj.iupac = str(nextline.strip().decode('ascii'))
                        motif_obj.length = len(str(nextline.strip().decode('ascii')))
                        motif_obj.save()
                        sys.stdout.flush()

                    process.wait()

                    print("IUPAC=" + motif_obj.iupac )
                    print("LENGTH=" + str(motif_obj.length))

                    # calculate db matches
                    # db_matches = models.ManyToManyField(ChIPseq)
                    job.status = 'DB matches for motif #%s ...' % motif
                    job.save()
                    print(datetime.datetime.now(), "\t | update: \t %s " % job.status )

                    # get DBParams
                    db_param = get_object_or_404(DbParameter, param_id=100)
                    read_order = 0 # we only compare 0-th order models since this makes reverseComplement calculation easy and fast
                    print("READ_ORDER=" + str(read_order))
                    command = 'R --slave --no-save < /code/bammmotif/static/scripts/bamm_match.R --args' + ' --p_val_limit=' + str(job.p_value_cutoff) + ' --shuffle_times=' + str(10) + ' --read_order=' + str(read_order) + ' --db_order=' + str(db_param.modelorder) + ' --order=' + str(job.model_Order) + ' --query=' +  str(opath) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif) + '.ihbcp' + ' --bg='  +  str(opath) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '.hbcp' + ' --db_folder=/code/DB/ENCODE_ChIPseq/Results'
                    #command = 'python3 /code/bammmotif/static/scripts/tomtomtool.py ' +  opath + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif) + '.ihbcp ' + opath + '/' +  basename(os.path.splitext(job.Input_Sequences.name)[0]) + '.hbcp ' + '/code/DB/ENCODE_ChIPseq/Results ' + str(job.model_Order) + ' --db_order ' + str(db_param.modelorder) + ' --read_order ' + str(read_order) + ' --shuffle_times ' + str(10) + ' --quantile ' + str(0.1) +  ' --p_val_limit ' + str(job.p_value_cutoff)
                    print(command)
                    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                    # Poll process for new output until finished
                    while True:
                        nextline = process.stdout.readline()
                        if nextline == b'' and process.poll() is not None:
                            break
                        sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                        sys.stdout.flush()
                        if str(nextline.strip().decode('ascii')) == 'no matches!':
                            print('Comparison with database did not provide any matches!')
                            break
                        else:
                            match_name = str(nextline.strip().decode('ascii').split()[0])
                            print('MATCHNAME =' + match_name)
                            db_match = get_object_or_404(ChIPseq, filename=match_name)
                            # create relationship
                            rel_obj = DbMatch(
                                motif=motif_obj,
                                db_entry=db_match,
                                p_value=float(nextline.strip().decode('ascii').split()[1]),
                                e_value=float(nextline.strip().decode('ascii').split()[2]),
                                score=float(nextline.strip().decode('ascii').split()[3]),
                                overlap_len=int(float(nextline.strip().decode('ascii').split()[4]))
                            )
                            rel_obj.save()
                            motif_obj.save()

                    process.wait()

                    # print fdr and position plots plus zipping
                    if job.FDR == True:
                        job.status = 'FDR Position Plots for motif #%s ... ' % motif
                        job.save()
                        print(datetime.datetime.now(), "\t | update: \t %s " % job.status )

                        command = 'R --slave --no-save < /code/bammmotif/static/scripts/FDRplot_simple.R --args --output_dir=' + os.path.join(settings.MEDIA_ROOT, str(job_pk)) + ' --file_name_in=' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif) + ' --revComp='+ str(job.reverse_Complement) + ' --fasta_file_name=' + basename(job.Input_Sequences.name)
                        print(command)
                        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        # Poll process for new output until finished
                        nextline = process.stdout.readline()
                        sys.stdout.write("AUC = " + str(nextline.strip()) + "\n")
                        motif_obj.auc = float(nextline.strip())
                        sys.stdout.flush()
                        nextline = process.stdout.readline()
                        sys.stdout.write("OCC = " + str(nextline.strip()) + "\n")
                        motif_obj.occurrence = float(nextline.strip())
                        motif_obj.save()
                        sys.stdout.flush()

                    # print logo plots plus zipping
                    job.status = 'Logo Plots for motif #%s ... ' % motif
                    job.save()
                    print(datetime.datetime.now(), "\t | update: \t %s " % job.status )
                    sys.stdout.flush()

                    basic_name = opath + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif)
                    logo_files = ""
                    for order in range(min(job.model_Order+1,4)):
                        # big_logo
                        logo_files = logo_files + basic_name + '-logo-order-' + str(order) + '-icColumnScale-icLetterScale.png '
                        command = 'R --slave --no-save < /code/bammmotif/static/scripts/Utils.plotHOBindingSitesLogo.R --args --output_dir=' + opath + ' --file_name=' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif) + ' --order=' + str(order)
                        print( 'PLOTTER= ' + command)
                        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        # Poll process for new output until finished
                        while True:
                            nextline = process.stdout.readline()
                            if nextline == b'' and process.poll() is not None:
                                break
                            sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                            sys.stdout.flush()
                        process.wait()


                    # create summary file
                    job.status = 'Summarizing motif #%s ...' % motif
                    job.save()
                    print(datetime.datetime.now(), "\t | update: \t %s " % job.status )

                    if job.FDR == True:
                        # zipping performance plots
                        command = 'zip '+ basic_name + '_performance.zip ' + basic_name +'_FDR.jpeg ' + basic_name + '_Positions.jpeg'
                        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        # Poll process for new output until finished
                        while True:
                            nextline = process.stdout.readline()
                            if nextline == b'' and process.poll() is not None:
                                break
                            sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                            sys.stdout.flush()

                        process.wait()


                    # zipping motif logos
                    command = 'zip '+ basic_name + '_logos.zip ' + logo_files
                    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    # Poll process for new output until finished
                    while True:
                        nextline = process.stdout.readline()
                        if nextline == b'' and process.poll() is not None:
                            break
                        sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                        sys.stdout.flush()
                    process.wait()


                    # ziping complete model
                    command = 'zip '+ basic_name + '.zip ' + basic_name + '.*'
                    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    # Poll process for new output until finished
                    while True:
                        nextline = process.stdout.readline()
                        if nextline == b'' and process.poll() is not None:
                            break
                        sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                        sys.stdout.flush()

                    process.wait()

                # zipping complete job
                command = 'zip '+ opath + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_complete.zip ' + opath + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '*'
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                # Poll process for new output until finished
                while True:
                    nextline = process.stdout.readline()
                    if nextline == b'' and process.poll() is not None:
                        break
                    sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                    sys.stdout.flush()

                #process.wait()

                '''
                # email user when job has finished
                if job.user.get_short_name() != 'Anonymous':
                    email_header = "BaMM! - your job has finished! ( " + job.name + " )"
                    email_message = "Dear " + job.user.get_short_name() + ", \n" + " your BaMM! job has successfully finished.\n" + "You can view your results following the link below:\n" + "https://bammmotif.mpibpc.mpg.de/results/" + str(job.job_ID) + "/\n\n" + " Greetings from the BaMM! -Team" 
                    job.user.email_user(email_header, email_message)
'''
                job.status = 'Successfully finished'
                job.save()
                print(datetime.datetime.now(), "\t | END: \t %s " % job.status )

                return 0

            except Exception as e:
                job.status = 'error'
                job.save()
                print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
                import traceback
                traceback.print_exc()
                return 1


@task(bind=True)
def run_example(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    opath = os.path.join(settings.MEDIA_ROOT, str(job_pk),"Output")

    for motif in range(1, (int(job.num_motifs)+1)):
        # generate new motif database entry for current motif
        motif_obj = Motifs( parent_job = job, job_rank = motif)
        motif_obj.save()

        # calculate iupac
        command = 'python3 /code/bammmotif/static/scripts/pwm2iupac.py ' + opath + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif) + '.ihbcp ' + str(job.model_Order)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline()
            if nextline == b'' and process.poll() is not None:
                break
            sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
            motif_obj.iupac = str(nextline.strip().decode('ascii'))
            motif_obj.length = len(str(nextline.strip().decode('ascii')))
            motif_obj.save()
            sys.stdout.flush()

        process.wait()

        # calculate db matches
        # db_matches = models.ManyToManyField(ChIPseq)

        # get DBParams
        db_param = get_object_or_404(DbParameter, param_id=100)
        read_order = 0 # we only compare 0-th order models since this makes reverseComplement calculation easy and fast
        command = 'R --slave --no-save < /code/bammmotif/static/scripts/bamm_match.R --args' + ' --p_val_limit=' + str(job.p_value_cutoff) + ' --shuffle_times=' + str(10) + ' --read_order=' + str(read_order) + ' --db_order=' + str(db_param.modelorder) + ' --order=' + str(job.model_Order) + ' --query=' +  str(opath) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif) + '.ihbcp' + ' --bg='  +  str(opath) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '.hbcp' + ' --db_folder=/code/DB/ENCODE_ChIPseq/Results'
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline()
            if nextline == b'' and process.poll() is not None:
                break
            sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
            sys.stdout.flush()
            if str(nextline.strip().decode('ascii')) == 'no matches!':
                print('Comparison with database did not provide any matches!')
                break
            else:
                match_name = str(nextline.strip().decode('ascii').split()[0])
                db_match = get_object_or_404(ChIPseq, filename=match_name)
                # create relationship
                rel_obj = DbMatch(
                    motif=motif_obj,
                    db_entry=db_match,
                    p_value=float(nextline.strip().decode('ascii').split()[1]),
                    e_value=float(nextline.strip().decode('ascii').split()[2]),
                    score=float(nextline.strip().decode('ascii').split()[3]),
                    overlap_len=int(float(nextline.strip().decode('ascii').split()[4]))
                )
                rel_obj.save()
                motif_obj.save()
        process.wait()

        # print fdr and position plots plus zipping
        if job.FDR == True:
            command = 'R --slave --no-save < /code/bammmotif/static/scripts/FDRplot_simple.R --args --output_dir=' + os.path.join(settings.MEDIA_ROOT, str(job_pk)) + ' --file_name_in=' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif) + ' --revComp='+ str(job.reverse_Complement) + ' --fasta_file_name=' + basename(job.Input_Sequences.name)
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # Poll process for new output until finished
            nextline = process.stdout.readline()
            sys.stdout.write("AUC = " + str(nextline.strip()) + "\n")
            motif_obj.auc = float(nextline.strip())
            sys.stdout.flush()
            nextline = process.stdout.readline()
            sys.stdout.write("OCC = " + str(nextline.strip()) + "\n")
            motif_obj.occurrence = float(nextline.strip())
            motif_obj.save()
            sys.stdout.flush()
    return 0


@task(bind=True)
def run_peng(self, job_pk):
    print("inside peng motif")
    job = get_object_or_404(Job, pk=job_pk)
    try:
        job.status = 'Initializing with PEnGmotif'
        job.save()
        check = subprocess.Popen(['/code/bammmotif/static/scripts/peng_motif',
                                  str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name)),
                                  '-o', str(os.path.join(settings.MEDIA_ROOT, str(job.pk),"Input/", "MotifInitFile.peng"))],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        check.wait()

        f = open(str(os.path.join(settings.MEDIA_ROOT, str(job.pk),'Input/', 'MotifInitFile.peng')))
        job.Motif_InitFile.save("MotifInitFile.peng", File(f))
        job.Motif_Init_File_Format = "PWM"
        job.status = "PEnGmotif finished"
        job.save()

        print("peng worked")
        return 0

    except Exception as e:
        job.status = 'error'
        job.save()

        print("peng crashed")
        return 1

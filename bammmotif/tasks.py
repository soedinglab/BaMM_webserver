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

#@task(bind=True)
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
        job.status = 'invalit initialization file'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1

#@task(bind=True)
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
        job.status = 'invalid fasta file'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1

#@task(bind=True)
def PeNG_command(self,job_pk):
    job =  get_object_or_404(Job, pk=job_pk)
    try:
        job.status = 'Running PEnGmotif'
        job.save() 
        print(datetime.datetime.now(), "\t | START: \t %s " % job.status )
        # something is wrong with the permission, it doesn't help to add shoot peng to the paths
        # also the new paths are not set for the plotting scripts so shootpeng refuses
        # Wanwan,Slack:For running shoot_peng.py , you need three additional binaries/script, namely:  
        # peng_motif, FDR and evaluateBaMM.R (plotAUSFC_benchmark_fdrtool.R is replaced by evaluateBaMM.R).
        # peng_motif can be found in PEnGmotif project and FDR and evaluateBaMM.R can be found in BaMM project
        # you just need to adjust the paths in the shoot_peng.py to find these three files.
        # python3 ${SHOOT_PENG} ${FASTA_DIR}/$f -d ${outdir} -o ${outdir}/${bn}.meme --iupac_optimization_score MUTUAL_INFO > ${outdir}/${bn}.logg
        # ${FDR} ${outdir}/ ${FASTA_DIR}/${bn}.fasta --PWMFile ${outdir}/${bn}.meme --num 1 -k 0 --cvFold 1
        # Rscript ${AUSFC_SCRIPT} ${outdir} ${bn}
        opath = os.path.join(settings.MEDIA_ROOT, str(job_pk),"Input")

        command = 'python3 shoot_peng.py ' + str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name)) + ' -d ' + opath + ' -o ' +  opath + '/MotifInitFile.peng' + ' --iupac_optimization_score MUTUAL_INFO'
        print( "\n COMMAND =  %s \n" % command )
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
        f.close()

        job.Motif_Init_File_Format = "PWM"
        job.status = "PEnGmotif finished"
        job.save()
        print(datetime.datetime.now(), "\t | update: \t %s " % job.status )
        sys.stdout.flush()
        return 0        
    
    except Exception as e:
        job.status = 'error running PEnG!motif'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1
    
def BaMM_command(self,job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    try:
        job.status = "Preparing for BaMM!motif"
        job.save()
        if job.Motif_Initialization == "PEnGmotif":
            print(datetime.datetime.now(), "\t | update: \t %s " % job.status )
        else:
            print(datetime.datetime.now(), "\t | START: \t %s " % job.status )

        opath = os.path.join(settings.MEDIA_ROOT, str(job_pk),"Output")
        params = opath + " " + str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))
        # optional Files
        if str(job.Background_Sequences.name) != '':
            params = params + " --negSeqFile " +  os.path.join(settings.MEDIA_ROOT, job.Background_Sequences.name)
        if str(job.Intensity_File.name) != '':
            params = params + " --intensityFile " + os.path.join(settings.MEDIA_ROOT, job.Intensity_File.name)
       
        # motif Initialization File
        if str(job.Motif_Init_File_Format) == "BindingSites":
            params = params + " --bindingSiteFile " + os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)
        if str(job.Motif_Init_File_Format) == "PWM":
            params = params + " --PWMFile " + os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)
        if str(job.Motif_Init_File_Format) == "BaMM":
            params = params + " --BaMMFile " + os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)

        #set enrichment parameters
        if str(job.mode) == "Occurrence":
            if( str(job.Motif_Init_File_Format) == "BaMM"):
                getModelOrder(self, job_pk, str("model"))
                params = params + " --bgModelFile " + os.path.join(settings.MEDIA_ROOT, job.bgModel_File.name)
                getModelOrder(self, job_pk, str("bg"))
            else:
                job.model_Order = 0
                job.background_Order = 0

            job.EM = False
            job.CGS = False
            job.FDR = False
            job.extend_1 = 0
            job.extend_2 = 0
            job.score_Seqset = True
       
         # general options
        params = params +  " --order " + str(job.model_Order)
        if job.reverse_Complement == False:
            params = params +  " --ss "
        params = params + " --Order " +  str(job.background_Order)
        params = params + " --alphabet " + str(job.alphabet)
        params = params + " --extend " + str(job.extend_1) +  " " +  str(job.extend_2)

        # fdr related options
        if job.FDR == True:
            params = params + " --FDR "
            params = params + " --savePRs "
            params = params + " --zoops "
            params = params + " --mFold " + str(job.m_Fold)
            params = params + " --cvFold " + str(job.cv_Fold)
            params = params + " --sOrder " + str(job.sampling_Order)

       # EM related options:
        if job.EM == True:
            params = params + " --EM "
            # these parameters do not exist anymore in the current version
            #params = params + " --epsilon " + str(job.epsilon)
            #params = params + " --maxEMIterations " + str(job.max_EM_Iterations)

        # Output related options:
        if job.verbose == True:
            params = params + " --verbose "
        if job.save_LogOdds == True:
            params = params + " --saveLogOdds "
        if job.save_BaMMs == True:
            params = params + " --saveBaMMs "
        if job.save_BgModel == True:
            params = params + " --saveBgModel "
        if job.score_Seqset == True:
            params = params + " --scoreSeqset "
            params = params + " --scoreCutoff " + str(job.score_Cutoff)

        job.status = 'Running BaMM'
        job.save() 
        print(datetime.datetime.now(), "\t | update: \t %s " % job.status )

        command = 'BaMMmotif ' + params
        print( "\n %s \n" % command )
        sys.stdout.flush()

        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline()
            if nextline == b'' and process.poll() is not None:
                break
            sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
            sys.stdout.flush()
        process.wait()    

        return 0

    except Exception as e:
        job.status = 'error running BaMM!motif'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1

def FDR_command(self,job_pk, motif):
    try:
        job = get_object_or_404(Job, pk=job_pk)
        job.status = 'False Discovery Estimation'
        job.save() 
        print(datetime.datetime.now(), "\t | update: \t %s " % job.status )

        opath = os.path.join(settings.MEDIA_ROOT, str(job_pk),"Output")
        print( 'OPATH= ' + opath)
        sys.stdout.flush()

        # get current motif obj to write AUSFC and OCCURRENCE
        motif_obj = get_object_or_404(Motifs, pk=motif_pk)

        # currently only for plotting since the calculation is done during the de-novo bammmotif call
        command = 'evaluateBaMM.R ' + opath + ' ' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + ' --SFC 1 --ROC5 1 --PRC 1'
        print(command)
        sys.stdout.flush()
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Poll process for new output until finished
        nextline = process.stdout.readline()
        sys.stdout.write("AUSFC = " + str(nextline.strip()) + "\n")
        motif_obj.auc = float(nextline.strip())
        sys.stdout.flush()
            #nextline = process.stdout.readline()
            #sys.stdout.write("OCC = " + str(nextline.strip()) + "\n")
            #motif_obj.occurrence = float(nextline.strip())
            #motif_obj.save()
            #sys.stdout.flush()
        
        # plot Motif Distribution
        command = 'plotMotifDistribution.R ' + opath + '/ ' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif)
        print(command)
        sys.stdout.flush()
        
        if job.reverse_Complement == False:
            command = command + ' --ss 1'
        print(command)
        sys.stdout.flush()
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline()
            if nextline == b'' and process.poll() is not None:
                break
            sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
            sys.stdout.flush()
        process.wait()

        return 0

    except Exception as e:
        job.status = 'error running BaMM!motif'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1

def PWM2IUPAC(self,job_pk,motif, motif_pk):
    try:
        job = get_object_or_404(Job, pk=job_pk)
        job.status = 'IUPAC for motif #%s ...' % motif
        job.save() 
        print(datetime.datetime.now(), "\t | update: \t %s " % job.status )

        motif_obj = get_object_or_404(Motifs, pk=motif_pk)
        opath = os.path.join(settings.MEDIA_ROOT, str(job_pk),"Output")

        # calculate iupac
        command = 'IUPAC.py ' + opath + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif) + '.ihbcp ' + str(job.model_Order)
        print(command)
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

        return 0

    except Exception as e:
        job.status = 'error calculating IUPAC'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1

def getModelOrder(self,job_pk, mode):
    try:
        job = get_object_or_404(Job, pk=job_pk)
        
        if str(mode) == 'model':
            # find out model Order of init file if not given
            command = 'python3 /ext/bin/getModelOrder.py ' + os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # Poll process for new output until finished
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

        if str(mode) == 'bg':
            # find out background model order
            command = 'python3 /ext/bin/getbgModelOrder.py ' + os.path.join(settings.MEDIA_ROOT, job.bgModel_File.name)
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

        return 0

    except Exception as e:
        job.status = 'error obtaining modelOrder'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1

def MMcompare(self,job_pk, motif, motif_pk):
    try:
        job = get_object_or_404(Job, pk=job_pk)
        job.status = 'Motif-motif comparison for Motif #%s ...' % motif
        job.save() 
        print(datetime.datetime.now(), "\t | update: \t %s " % job.status )

        motif_obj = get_object_or_404(Motifs, pk=motif_pk)
        
        opath = os.path.join(settings.MEDIA_ROOT, str(job_pk),"Output")
        
        # get DBParams
        db_param = get_object_or_404(DbParameter, param_id=100)
        read_order = 0 # we only compare 0-th order models since this makes reverseComplement calculation easy and fast
        print("READ_ORDER=" + str(read_order))
        command = 'MMcompare.R --args' + ' --p_value=' + str(job.p_value_cutoff) + ' --sampling=' + str(20) + ' --readOrder=' + str(read_order) + ' --dbOrder=' + str(db_param.modelorder) + ' --qOrder=' + str(job.model_Order) + ' --query=' +  str(opath) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif) + '.ihbcp' + ' --bg='  +  str(opath) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '.hbcp' + ' --dbDir=/code/DB/ENCODE_ChIPseq/Results'
        print(command)
        sys.stdout.flush()

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
        return 0

    except Exception as e:
        job.status = 'error in MMcompare'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1

def LogoPlotting(self,job_pk, motif):
    try:
        job = get_object_or_404(Job, pk=job_pk)
        # print logo plots plus zipping
        job.status = 'Logo Plots for motif #%s ... ' % motif
        job.save() 
        print(datetime.datetime.now(), "\t | update: \t %s " % job.status )
        sys.stdout.flush()
        
        opath = os.path.join(settings.MEDIA_ROOT, str(job_pk),"Output")

        basic_name = opath + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif)
        for order in range(min(job.model_Order+1,4)): 
            if order == 0:
                # plot reverseComplement
                command = 'plotBaMMLogo.R ' + basic_name + '.ihbcp ' + str(order) + ' --revComp 1'
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
    
                # plot reverse Complement as Stamp version
                command = 'plotBaMMLogo.R ' + basic_name + '.ihbcp ' + str(order) + ' --revComp 1 --stamp 1'
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

                # plot stamp version
                command = 'plotBaMMLogo.R ' + basic_name + '.ihbcp ' + str(order) + ' --stamp 1'
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

            # plot logo with axis and title
            command = 'plotBaMMLogo.R ' + basic_name + '.ihbcp ' + str(order)
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

        return 0

    except Exception as e:
        job.status = 'error Logo Plotting'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1

@task(bind=True)
def runDiscovery(self, job_pk):
    try:
        job = get_object_or_404(Job, pk=job_pk)
        # first define log file for redirecting output information
        logfile =   str(settings.MEDIA_ROOT) + "/logs/" + str(job_pk) + ".log"
        with open(logfile, 'w') as f:
            with redirect_stdout(f):
                if job.Motif_Initialization == "PEnGmotif":
                    print( "shortly before entering PeNG_command")
                    PeNG_command(self, job_pk)
                    print( "finished PeNG_command")

                BaMM_command(self, job_pk)
                
                opath = os.path.join(settings.MEDIA_ROOT, str(job_pk),"Output")
                job.num_motifs  = (len(os.listdir(opath))-2)/5
                
                for motif in range(1, (int(job.num_motifs)+1)):
                    processMotif(self, job_pk, motif)

                # compress job related info
                Compress(self, job_pk, 0)

        job.status = 'Successfully finished'
        job.save()
        print(datetime.datetime.now(), "\t | END: \t %s " % job.status )
        sys.stdout.flush()
        return 0

    except Exception as e:
        job.status = 'error running Discovery'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1       

@task(bind=True)
def runComparison(self, job_pk):
    try:
        job = get_object_or_404(Job, pk=job_pk)
        # first define log file for redirecting output information
        logfile =   str(settings.MEDIA_ROOT) + "/logs/" + str(job_pk) + ".log"
        with open(logfile, 'w') as f:
            with redirect_stdout(f):
                BaMM_command(self, job_pk)
                opath = os.path.join(settings.MEDIA_ROOT, str(job_pk),"Output")
                job.num_motifs  = (len(os.listdir(opath))-2)/5
                for motif in range(1, (int(job.num_motifs)+1)):
                    motif_obj = Motifs( parent_job = job, job_rank = motif)
                    PWM2IUPAC(self, job_pk, motif, motif_obj.moti_ID)
                    MMCompare(self, job_pk, motif)
                    # plot Logos
                    LogoPlotting(self,job_pk, motif)
                    # compress motif related info
                    Compress(self,job_pk, motif )

                # compress job related info
                Compress(self, job_pk, 0)

        job.status = 'Successfully finished'
        job.save()
        print(datetime.datetime.now(), "\t | END: \t %s " % job.status )
        sys.stdout.flush()
        return 0

    except Exception as e:
        job.status = 'error running Discovery'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1

def processMotif(self,job_pk, motif):
    try:
        job = get_object_or_404(Job, pk=job_pk)
        job.status = 'Processing motif #%s ...' % motif
        job.save() 
        print(datetime.datetime.now(), "\t | update: \t %s " % job.status )

        # generate new motif database entry for current motif
        motif_obj = Motifs( parent_job = job, job_rank = motif)
        motif_obj.save()
        
        # get IUPAC and motif length
        PWM2IUPAC(self,job_pk, motif, motif_obj.motif_ID)

        # get motif motif comparison to database
        MMcompare(self,job_pk, motif, motif_obj.motif_ID)

        if job.FDR == True:
            # plot FDR outcome
            FDR_command(self,job_pk, motif)

        # plot Logos
        LogoPlotting(self,job_pk, motif)
        
        # compress motif related info
        Compress(self,job_pk, motif )

        return 0

    except Exception as e:
        job.status = 'error processing Motif'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1       

def Compress(self,job_pk, motif):
    try:
        job = get_object_or_404(Job, pk=job_pk)
        opath = os.path.join(settings.MEDIA_ROOT, str(job_pk),"Output")
        if motif == 0:
            job.status = 'Compressing Results ...' 
            job.save() 
            print(datetime.datetime.now(), "\t | update: \t %s " % job.status )
            command = 'zip '+ opath + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_complete.zip ' + opath + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '*' 
            print(command)
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # Poll process for new output until finished
            while True:
                nextline = process.stdout.readline()
                if nextline == b'' and process.poll() is not None:
                    break
                sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                sys.stdout.flush()
            process.wait()

        else:
            job.status = 'Summarizing motif #%s ...' % motif
            job.save() 
            print(datetime.datetime.now(), "\t | update: \t %s " % job.status )
            basic_name = opath + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_' + str(motif)

            if job.FDR == True:
                # zipping performance plots
                command = 'zip '+ basic_name + '_performance.zip ' + basic_name +'_SFC.jpeg ' + basic_name + '_distribution.jpeg ' + basic_name + '_PRC.jpeg ' + basic_name + '_pROC.jpeg '
                print(command)
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
            command = 'zip '+ basic_name + '_logos.zip ' + basic_name + '-logo-order-*'
            print(command)
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
            command = 'zip '+ basic_name + '.zip ' + basic_name + '*' 
            print(command)
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # Poll process for new output until finished
            while True:
                nextline = process.stdout.readline()
                if nextline == b'' and process.poll() is not None:
                    break
                sys.stdout.write(str(nextline.strip().decode('ascii')) + "\n")
                sys.stdout.flush()
            process.wait()
            
        return 0

    except Exception as e:
        job.status = 'error Compressing'
        job.save()
        print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status )
        return 1       

@task(bind=True)
def run_bamm(self, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    # first define log file for redirecting output information
    logfile =   str(settings.MEDIA_ROOT) + "/logs/" + str(job_pk) + ".log"
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
                    f.close()
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
        f.close()
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

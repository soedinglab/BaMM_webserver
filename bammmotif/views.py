from django.conf import settings
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.utils.encoding import smart_str
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.core.files import File
from django.http import HttpResponse
from .models import *
from .forms import *
from .tasks import *
from ipware.ip import get_ip
import datetime
import subprocess
import os
import sys


##########################
### HOME and GENERAL VIEWS
##########################

def home(request):
    return render(request, 'home/home.html')

def info(request):
    return render(request, 'home/aboutBaMMmotif.html')

def documentation(request):
    return render(request, 'home/documentation.html')

def download(request):
    return render(request, 'home/download.html')
    
def contact(request):
    return render(request, 'home/contact.html')
    
def imprint(request):
    return render(request, 'home/imprint.html')

##########################
### JOB RELATED VIEWS
##########################

def data_predict(request):
    print("ENTERING Data PREDICT VIEW")
    if request.method == "POST":
        print("Request IST POST")
        form = JobForm(request.POST, request.FILES)
        
        if form.is_valid():
            print("FORM IS VALID")
            # Test if data maximum size is not reached
            content = form.cleaned_data['Input_Sequences']
            if request.user.is_authenticated():
                if content._size > int(settings.MAX_UPLOAD_SIZE):
                    form = JobForm()
                    return render(request, 'job/de_novo_search.html', {'form':form , 'type' : "FileSize", 'message' : settings.MAX_UPLOAD_SIZE})
            else:
                if content._size > int(settings.MAX_UPLOAD_SIZE_ANONYMOUS):
                    form = JobForm()
                    return render(request, 'job/de_novo_search.html', {'form':form , 'type' : "FileSize", 'message' : settings.MAX_UPLOAD_SIZE_ANONYMOUS })

            job = form.save(commit=False)
            job.created_at = datetime.datetime.now()
            job.status = "data uploaded"
            if request.user.is_authenticated():
                print("user is authenticated")
                job.user = request.user
            else:
                print("User is not authenticated")
                ip = get_ip(request)
                if ip is not None:
                    print("we have an IP address for user")
                    # check if anonymous user already exists
                    anonymous_users = User.objects.filter(username=ip)
                    if anonymous_users.exists():
                        print("user already exists")
                        job.user = get_object_or_404(User, username=ip)
                    else:
                        print("create new anonymous user")
                        # create an anonymous user and log them in
                        username = ip
                        u = User(username=username, first_name='Anonymous', last_name='User')
                        u.set_unusable_password()
                        u.save()
                        #login(request, u)
                        job.user = u
                else:
                    print("we don't have an IP address for user")

            print("UPLOAD COMPLETE: save job object")
            job.save() 
            print("JOB ID = ", str(job.pk))
            
            # check if job has a name, if not use first 6 digits of job_id as job_name
            if job.job_name == None:
                # truncate job_id
                job_id_short = str(job.job_ID).split("-",1)
                job.job_name = job_id_short[0]
                job.save() 


            #check if file formats are correct
            opath = os.path.join(settings.MEDIA_ROOT, str(job.pk),"Output")
            
            # 1. Input sequence File
            check = subprocess.Popen(['/code/bammmotif/static/scripts/valid_fasta',
             str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))], 
             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = check.communicate()
              
            out = out.decode('ascii')
           
            if out == "OK":
                # 2. Background Sequence File
                if job.Background_Sequences.name == None:
                    out = "OK"
                else:                
                    check = subprocess.Popen(['/code/bammmotif/static/scripts/valid_fasta',
                    str(os.path.join(settings.MEDIA_ROOT, job.Background_Sequences.name))], 
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    out, err = check.communicate()  
                    out = out.decode('ascii')
          
                if out == "OK":  
                
                    # optional: run PEnGmotif to maintain Motif Init File
                    #if str(job.Motif_Initialization) == "PEnGmotif":
                    #    print("RUNNING PENG!MOTIF USING CELERY TASK")
                        #task = run_bamm.delay(job.pk)
                        #task = test_R.delay(job.pk)
                    #    task = run_peng.delay(job.pk)
                    #    print("FINISHED PENG MOTIF USING CELERY")
                        #check = subprocess.Popen(['/code/bammmotif/static/scripts/peng_motif',    
                        #str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name)),
                        #'-o', str(os.path.join(settings.MEDIA_ROOT, str(job.pk),"Input/", "MotifInitFile.peng"))],             
                        #stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        #out, err = check.communicate()  
                        #out = out.decode('ascii')

                        #f = open(str(os.path.join(settings.MEDIA_ROOT, str(job.pk),'Input/', 'MotifInitFile.peng')))
                        #job.Motif_InitFile.save("MotifInitFile.peng", File(f))
                        #job.Motif_Init_File_Format = "PWM"
                        #job.save()
                    #else:
                    # 3. Motif Init File 
                    #    check = subprocess.Popen(['/code/bammmotif/static/scripts/valid_Init',
                    #    str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name)),
                    #    str(os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)),
                    #    str(job.Motif_Init_File_Format) ], 
                    #    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    #    out, err = check.communicate()  
                    #    out = out.decode('ascii')
                    
                    if out == "OK":
                        print("OUT IS OK -> run the JOB")
                        run_bamm.delay(job.pk)
                        #run_bamm_direct.delay(job.pk)
                        return render(request, 'job/submitted.html', {'pk': job.pk} ) 
                        #return redirect('run_job', pk=job.pk)  
                    else:
                        print("OUT IS NOT OK -> delete job and give error message 1")
                        Job.objects.filter(job_ID=job.pk).delete()
                        form = JobForm()
                        return render(request, 'job/de_novo_search.html', {'form':form , 'type' : "Init", 'message' : out })
                else:
                    print("OUT IS NOT OK -> delete job and give error message 2")
                    Job.objects.filter(job_ID=job.pk).delete()
                    form = JobForm()
                    return render(request, 'job/de_novo_search.html', {'form':form , 'type' : "Background", 'message' : out })
            else:
                print("OUT IS NOT OK -> delete job and give error message 3")
                print(out)
                Job.objects.filter(job_ID=job.pk).delete()
                form = JobForm()
                return render(request, 'job/de_novo_search.html', {'form':form , 'type' : "Fasta", 'message' : out })
        else:
            print("Form is not valid")
            form = JobForm()
            return render(request, 'job/de_novo_search.html', {'form':form , 'type' : "OK", 'message' : "OK"})

    else:
        print("Request IS NOT POST -> make form and redirect")
        form = JobForm()
        return render(request, 'job/de_novo_search.html', {'form':form , 'type' : "OK", 'message' : "OK"})

    print("default action applies")
    return render(request, 'job/de_novo_search.html', {'form':form , 'type' : "OK", 'message' : "OK"})
'''
def run_job(request,pk):
    job = get_object_or_404(Job, pk=pk)    
    opath = os.path.join(settings.MEDIA_ROOT, str(job.pk),"Output")
    #subprocess.Popen(['/code/bammmotif/static/scripts/runBaMMmotif.sh', 
    # str(opath),
    # str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name)), 
    # str(os.path.join(settings.MEDIA_ROOT, job.Background_Sequences.name)),
    # str(job.alphabet),
    # str(job.reverse_Complement),
    # str(os.path.join(settings.MEDIA_ROOT, job.Intensity_File.name)), 
    # str(job.Motif_Initialization),
    # str(os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)), 
    # str(job.Motif_Init_File_Format),
    # str(job.model_Order),
    # str(job.extend_1),
    # str(job.extend_2),
    # str(job.background_Order),
    # str(job.EM),
    # str(job.max_EM_Iterations),
    # str(job.epsilon),
    # str(job.q_value),
    # str(job.no_Alpha_Optimization),
    # str(job.FDR),
    # str(job.m_Fold),
    # str(job.cv_Fold),
    # str(job.sampling_Order),
    # str(job.save_LogOdds),
    # str(job.CGS),
    # str(job.max_CGS_Iterations),
    # str(job.no_Alpha_Sampling),
    # str(job.verbose),
    # str(job.save_BaMMs),
	# str(job.job_ID),
	# str(settings.DB_HOST),
	# str(settings.DB_NAME),
	# str(settings.DB_USER),
	# str(settings.DB_PW),
	# str("bammmotif_job"),
    # str(job.db_match_bit_factor),
    # ])
    job.status = "Submitted"
    job.save() 
    return render(request, 'job/submitted.html', {'pk': pk} ) 
'''
def data_discover(request):
    if request.method == "POST":
        form = DiscoveryForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_at = datetime.datetime.now()
            job.status = "data uploaded"
            if request.user.is_authenticated():
                print("user is authenticated")
                job.user = request.user
            else:
                print("User is not authenticated")
                ip = get_ip(request)
                if ip is not None:
                    print("we have an IP address for user")
                    # check if anonymous user already exists
                    anonymous_users = User.objects.filter(username=ip)
                    if anonymous_users.exists():
                        print("user already exists")
                        job.user = get_object_or_404(User, username=ip)
                    else:
                        parint("create new anonymous user")
                        # create an anonymous user and log them in
                        username = ip
                        u = User(username=username, first_name='Anonymous', last_name='User')
                        u.set_unusable_password()
                        u.save()
                        login(request, u)
                        job.user = u
                else:
                    print("we don't have an IP address for user")
            job.save() 

            #check if file formats are correct
            opath = os.path.join(settings.MEDIA_ROOT, str(job.pk),"Output")
            
            # 1. Input sequence File
            check = subprocess.Popen(['/code/bammmotif/static/scripts/valid_fasta',
             str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))], 
             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = check.communicate()
              
            out = out.decode('ascii')

            if out == "OK":
                return redirect('overview_discover', pk=job.pk)  
            else:
                job.delete()
                form = DiscoveryForm()
                return render(request, 'job/data_dicover.html', {'form':form , 'type' : "Fasta", 'message' : out })
        else:
            form = DiscoveryForm()
    else:
        form= DiscoveryForm()
    return render(request, 'job/data_discover.html', { 'form':form })

def data_discover_from_db(request, pk):
    db_entry = get_object_or_404(ChIPseq, pk=pk)
    if request.method == "POST":
        form=DiscoveryDBForm(request.POST, request.FILES)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_at = datetime.datetime.now()
            job.status = "data uploaded"
            if request.user.is_authenticated():
                print("user is authenticated")
                job.user = request.user
            else:
                print("User is not authenticated")
                ip = get_ip(request)
                if ip is not None:
                    print("we have an IP address for user")
                    # check if anonymous user already exists
                    anonymous_users = User.objects.filter(username=ip)
                    if anonymous_users.exists():
                        print("user already exists")
                        job.user = get_object_or_404(User, username=ip)
                    else:
                        parint("create new anonymous user")
                        # create an anonymous user and log them in
                        username = ip
                        u = User(username=username, first_name='Anonymous', last_name='User')
                        u.set_unusable_password()
                        u.save()
                        login(request, u)
                        job.user = u
                else:
                    print("we don't have an IP address for user")
            job.save() 
            
            filename= str(db_entry.parent.base_dir) + '/Results/' + str(db_entry.result_location) + '/' + str(db_entry.result_location) + '_motif_1.ihbcp'
            f = open(str(filename))
            out_filename = str(db_entry.result_location) + ".ihbcp"
            job.Motif_InitFile.save(out_filename , File(f))
            job.Motif_Init_File_Format = "BaMM"
            job.save()
            
            #check if file formats are correct
            opath = os.path.join(settings.MEDIA_ROOT, str(job.pk),"Output")
            
            # 1. Input sequence File
            check = subprocess.Popen(['/code/bammmotif/static/scripts/valid_fasta',
             str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))], 
             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = check.communicate()
              
            out = out.decode('ascii')

            if out == "OK":
                return redirect('overview_discover', pk=job.pk)  
            else:
                job.delete()
                form = DiscoveryDBForm()
                return render(request, 'job/data_discoverDB.html', {'form':form , 'type' : "Fasta", 'message' : out })

        else:
            form = DiscoveryDBForm()
    else:
        form = DiscoveryDBForm()
    return render(request, 'job/data_discoverDB.html',{'form': form, 'pk':pk, 'db_entry':db_entry})



def overview_discover(request, pk):
    job = get_object_or_404(Job, pk=pk)
    job.status = "job ready to submit" 
    # turn off optimization to just scan input sequence for model positions.
    job.EM = False
    job.CGS = False
    job.save()   
    return render(request, 'job/overview_discover.html', {'job':job, 'pk':pk})

def submitted(request,pk):
    return render(request, 'job/submitted.html', {'pk':pk})



##########################
### RESULT RELATED VIEWS
##########################



def find_results(request):
    if request.method == "POST":
        form = FindForm(request.POST)
        if form.is_valid():
            jobid = form.cleaned_data['job_ID']
            return redirect('result_detail', pk=jobid)  
    else:
        form = FindForm()
    return render(request, 'results/results_main.html', {'form':form})
    

def delete(request, pk ):
    Job.objects.filter(job_ID=pk).delete()
    if request.user.is_authenticated():
        user_jobs = Job.objects.filter(user = request.user.id)
        return render(request,'results/result_overview.html', { 'user_jobs' : user_jobs })
    else:
        return redirect(request,'find_results')

def result_detail(request, pk):
    result = get_object_or_404(Job, pk=pk)
    opath = os.path.join(settings.MEDIA_ROOT,str(result.pk),"Output")
    Output_filename, ending = os.path.splitext(os.path.basename(result.Input_Sequences.name))
    if result.status == 'Successfully finished':
        return render(request,'results/result_detail.html', {'result':result, 'opath':opath, 'Output_filename':Output_filename})
    else:
        command ="tail -20 /code/media/logs/" + pk + ".log"
        output = os.popen(command).read()
        return render(request,'results/result_status.html', {'result':result, 'opath':opath , 'output':output })

def result_overview(request):
    if request.user.is_authenticated():
        user_jobs = Job.objects.filter(user = request.user.id)
        return render(request,'results/result_overview.html', { 'user_jobs' : user_jobs })
    else:
        return redirect(request,'find_results')


##########################
### DATABASE RELATED VIEWS
##########################


def maindb(request):
    if request.method == "POST":
        form = DBForm(request.POST)
        if form.is_valid():
            protein_name = form.cleaned_data['db_ID']
            print('PROTEIN NAME= ' + protein_name)
            db_entries = ChIPseq.objects.filter( target_name__icontains=protein_name )
            print('LENGTH OF QUERRY= ' + str(len(db_entries)))
            db_entries = ChIPseq.objects.all()
            return render(request,'database/db_overview.html', {'protein_name':protein_name, 'db_entries':db_entries })
    else:
        form = DBForm()
    return render(request, 'database/db_main.html', {'form':form})

    

def db_overview(request, protein_name, db_entries):
    return render(request,'database/db_overview.html', {'protein_name':protein_name, 'db_entries':db_entries })

def db_detail(request, pk):
   entry = get_object_or_404(ChIPseq, db_public_id=pk)
   return render(request,'database/db_detail.html', {'entry':entry})








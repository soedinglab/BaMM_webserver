from django.conf import settings
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.utils.encoding import smart_str
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.core.files import File
from django.http import HttpResponse
from django.views.generic import TemplateView
from .models import *
from .forms import *
from .tasks import *
from ipware.ip import get_ip
import plotly.offline as opy
import plotly.graph_objs as go
import datetime
import subprocess
import os
import sys

class Plot(TemplateView):
    template_name = 'results/result_detail.html'

    def get_context_data(self, **kwargs):
        context = super( Plot, self).get_context_data(**kwargs)
        
        # get Job object
        result = get_object_or_404(Job, pk=self.kwargs.get('pk',None))
        opath = os.path.join(settings.MEDIA_ROOT,str(result.pk),"Output")
        Output_filename, ending = os.path.splitext(os.path.basename(result.Input_Sequences.name))
        num_logos = range(min(2,result.model_Order) + 1)

        context['result'] = result
        context['opath'] = opath
        context['Output_filename'] = Output_filename
        context['num_logos'] = num_logos

        all_plots = {}

        NumMotifs = max(1, result.num_motifs)
        for m in range(NumMotifs):
            # read in logOdds Scores:
            score_file = opath + '/' + Output_filename + '_motif_' + str(m+1) + '.scores'
            data = {'start': [], 'end': [], 'score': [], 'pVal':[], 'eVal':[], 'strand': [], 'pattern': []}
            
            with open ( score_file ) as fh:
                for line in fh:
                    head = list(line)
                    if head[0] == ">":
                        #header line
                        print(line)
                    else:
                        tok = line.split ( ':' )
                        # start - end - score - pVal - eVal - strand - pattern :
                        data['start'].append(tok[0])
                        data['end'].append( tok[1] )
                        data['score'].append( tok[2] )
                        data['pVal'].append( tok[3] )
                        data['eVal'].append( tok[4] )
                        data['strand'].append ( tok[5] )
                        data['pattern'].append ( tok[6].strip() )


            #trace1 = go.Scatter(x=data['start'] , y= data['score'],marker={'color': 'red', 'symbol': 104, 'size': "10"},
            #                    mode="lines",  name='1st Trace')
            trace1 = go.Histogram(x=data['start'] )

            #x = [-2+m,0+m,4+m,6+m,7+m]
            #y = [q**2-q+3 for q in x]
            #trace1 = go.Scatter(x=x, y=y, marker={'color': 'red', 'symbol': 104, 'size': "10"},
            #                    mode="lines",  name='1st Trace')

            dat=go.Data([trace1])
            layout=go.Layout(title="Motif Occurrence", xaxis={'title':'Position on Sequence'}, yaxis={'title':'Counts'})
            figure=go.Figure(data=dat,layout=layout)
            div = opy.plot(figure, auto_open=False, output_type='div')

            all_plots[m+1]=div
  
        context['plot'] = all_plots


        return context


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

def get_correct_form(request, mode, example = False):
    print("MODE=" , mode)
    print("Example=" , example)
    # first check which job the user wants to perform and load the appropriate form 
    if str(mode) == "Prediction":
        if(request.method == "POST"):
            if example:
                form = PredictionExampleForm(request.POST, request.FILES)    
            else:
                form = PredictionForm(request.POST, request.FILES)
        else:
            if example:
                form = PredictionExampleForm()
            else:
                form = PredictionForm()

    elif str(mode) == "Occurrence":
        if(request.method == "POST"):
            if example:
                form = OccurrenceExampleForm(request.POST, request.FILES)    
            else:
                form = OccurrenceForm(request.POST, request.FILES)
        else:
            if example:
                form = OccurrenceExampleForm()    
            else:
                form = OccurrenceForm()

    elif str(mode) == "Compare":
        if(request.method == "POST"):
            if example:
                form = CompareExampleForm(request.POST, request.FILES)
            else:
                form = CompareForm(request.POST, request.FILES)
        else:
            if example:
                form = CompareExampleForm()
            else:
                form = CompareForm()

    else:
        return HttpResponseNotFound('<h1>Problem with the Job Request, please send an email describing what you did to bammmotif-info@mpg.de!</h1>')
    return form

def run_a_job(request, mode, example=False):
    form=get_correct_form(request, mode, example)    
    if request.method == "POST":
        if form.is_valid():
            # read in data and parameter
            job = form.save(commit=False)
            job.created_at = datetime.datetime.now()
            
            # assign user to new job instance
            if request.user.is_authenticated():
                job.user = request.user
            else:
                ip = get_ip(request)
                if ip is not None:
                    # check if anonymous user already exists
                    anonymous_users = User.objects.filter(username=ip)
                    if anonymous_users.exists():
                        job.user = get_object_or_404(User, username=ip)
                    else:
                        # create an anonymous user and log them in
                        username = ip
                        u = User(username=username, first_name='Anonymous', last_name='User')
                        u.set_unusable_password()
                        u.save()
                        job.user = u
                else:
                    print("we don't have an IP address for user")
            job.save() 

            # check if job has a name, if not use first 6 digits of job_id as job_name
            if job.job_name == None:
                # truncate job_id
                job_id_short = str(job.job_ID).split("-",1)
                job.job_name = job_id_short[0]
                job.save() 

            opath = os.path.join(settings.MEDIA_ROOT, str(job.job_ID),"Output")
            
            # if example is requested, load the sampleData
            if example:
                # load fasta file (needed for any job)
                filename= 'example_data/ExampleData.fasta'
                f = open(str(filename))
                out_filename = "ExampleData.fasta"
                job.Input_Sequences.save(out_filename , File(f))
                f.close()

                # load Initialization Motif
                filename= 'example_data/stuff/oneMotif.peng'
                f = open(str(filename))
                out_filename = "oneMotif.meme"
                job.Motif_InitFile.save(out_filename , File(f))
                f.close()

                job.Motif_Initialization = 'Custom File'
                job.Motif_Init_File_Format = 'PWM'
                job.save()
    
            # for occurrence search change MotifInitialization to being Custome file
            if mode == "Occurrence":
                job.Motif_Initialization = 'Custom File'
                job.save()

            #check if file formats are correct
            check_fasta = False
            # 1. Input sequence File
            if check_fasta:
                check = subprocess.Popen(['valid_fasta',
                    str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))], 
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out, err = check.communicate()
                out = out.decode('ascii')
            else:
                out = "OK"
            
            if out == "OK":
                job.status = "job ready to submit" 
                job.mode = str(mode)
                job.save()
                runJob.delay(job.job_ID)
                return render(request, 'job/submitted.html', {'pk': job.job_ID} )    
            else:
                job.delete()
                return render(request, 'job/data_input.html', {'form':form , 'mode':str(mode), 'example':example, 'type' : out })
    
    print("Form is not OK; mode=", mode, " example= ", example)
    return render(request, 'job/data_input.html', { 'form':form, 'mode':str(mode), 'example':example })

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
    
def result_overview(request):
    if request.user.is_authenticated():
        user_jobs = Job.objects.filter(user = request.user.id)
        return render(request,'results/result_overview.html', { 'user_jobs' : user_jobs })
    else:
        return redirect(request,'find_results')

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
        print("status is successfull")
        num_logos = range(1, (min(2,result.model_Order)+1))
        if result.mode == "Prediction" or result.mode =="Compare":
            return render(request,'results/result_detail.html', {'result':result, 'opath':opath, ',ode': result.mode, 'Output_filename':Output_filename, 'num_logos':num_logos})
        elif result.mode == "Occurrence":
            return redirect('result_occurrence', result.mode, pk)

    else:
        print('status not ready yet')
        command ="tail -20 /code/media/logs/" + pk + ".log"
        output = os.popen(command).read()
        return render(request,'results/result_status.html', {'result':result, 'opath':opath , 'output':output })


##########################
### DATABASE RELATED VIEWS
##########################


def maindb(request):
    if request.method == "POST":
        form = DBForm(request.POST)
        if form.is_valid():
            protein_name = form.cleaned_data['db_ID']
            db_entries = ChIPseq.objects.filter( target_name__icontains=protein_name )
            return render(request,'database/db_overview.html', {'protein_name':protein_name, 'db_entries':db_entries })
    else:
        form = DBForm()
    return render(request, 'database/db_main.html', {'form':form})

def db_overview(request, protein_name, db_entries):
    return render(request,'database/db_overview.html', {'protein_name':protein_name, 'db_entries':db_entries })

def db_detail(request, pk):
   entry = get_object_or_404(ChIPseq, db_public_id=pk)
   return render(request,'database/db_detail.html', {'entry':entry})


##########################
### VIEWS THAT CAN SOON BE DELETED
##########################

def OLD_data_predict(request):
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
            check = subprocess.Popen(['valid_fasta',
             str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))], 
             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = check.communicate()
              
            out = out.decode('ascii')
           
            if out == "OK":
                # 2. Background Sequence File
                if job.Background_Sequences.name == None:
                    out = "OK"
                else:                
                    check = subprocess.Popen(['valid_fasta',
                    str(os.path.join(settings.MEDIA_ROOT, job.Background_Sequences.name))], 
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    out, err = check.communicate()  
                    out = out.decode('ascii')
          
                if out == "OK":  
                
                    # 3. Motif Init File 
                    #    check = subprocess.Popen(['valid_Init',
                    #    #check = subprocess.Popen(['/code/bammmotif/static/scripts/valid_Init',
                    #    str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name)),
                    #    str(os.path.join(settings.MEDIA_ROOT, job.Motif_InitFile.name)),
                    #    str(job.Motif_Init_File_Format) ], 
                    #    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    #    out, err = check.communicate()  
                    #    out = out.decode('ascii')
                    
                    if out == "OK":
                        print("OUT IS OK -> run the JOB")
                        runDiscovery.delay(job.pk)
                        return render(request, 'job/submitted.html', {'pk': job.pk} ) 
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


def OLD_denovo_example(request):
    print("ENTERING Data PREDICT VIEW with example")
    if request.method == "POST":
        print("Request IST POST")
        form = ExampleForm(request.POST, request.FILES)
        
        if form.is_valid():
            print("FORM IS VALID")
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
                        job.user = u
                else:
                    print("we don't have an IP address for user")

            # upload motifInitFile
            filename= 'example_data/ExampleData.fasta'
            f = open(str(filename))
            out_filename = "ExampleData.fasta"
            job.Input_Sequences.save(out_filename , File(f))
            f.close()
            
            print("UPLOAD COMPLETE: save job object")
            job.save() 
            print("JOB ID = ", str(job.pk))
            
            # check if job has a name, if not use first 6 digits of job_id as job_name
            if job.job_name == None:
                # truncate job_id
                job_id_short = str(job.job_ID).split("-",1)
                job.job_name = job_id_short[0]
                job.save() 

            # 2. Background Sequence File
            if job.Background_Sequences.name == None:
                out = "OK"
            else:                
                check = subprocess.Popen(['valid_fasta',
                str(os.path.join(settings.MEDIA_ROOT, job.Background_Sequences.name))], 
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                out, err = check.communicate()  
                out = out.decode('ascii')
          
            if out == "OK":  
                print("OUT IS OK -> run the JOB")
                runDiscovery.delay(job.pk)
                return render(request, 'job/submitted.html', {'pk': job.pk} ) 
            else:
                print("OUT IS NOT OK -> delete job and give error message 2")
                Job.objects.filter(job_ID=job.pk).delete()
                form = ExampleForm()
                return render(request, 'job/de_novo_search_example.html', {'form':form , 'type' : "Background", 'message' : out })
        else:
            print("Form is not valid")
            form = ExampleForm()
            return render(request, 'job/de_novo_search_example.html', {'form':form , 'type' : "OK", 'message' : "OK"})
    else:
        print("Request IS NOT POST -> make form and redirect")
        form = ExampleForm()
        return render(request, 'job/de_novo_search_example.html', {'form':form , 'type' : "OK", 'message' : "OK"})

    print("default action applies")
    return render(request, 'job/de_novo_search_example.html', {'form':form , 'type' : "OK", 'message' : "OK"})


def OLD_motif_compare(request):
    if request.method == "POST":
        form = CompareForm(request.POST, request.FILES)
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
                        print("create new anonymous user")
                        # create an anonymous user and log them in
                        username = ip
                        u = User(username=username, first_name='Anonymous', last_name='User')
                        u.set_unusable_password()
                        u.save()
                        job.user = u
                else:
                    print("we don't have an IP address for user")
            job.save() 

            # check if job has a name, if not use first 6 digits of job_id as job_name
            if job.job_name == None:
                # truncate job_id
                job_id_short = str(job.job_ID).split("-",1)
                job.job_name = job_id_short[0]
                job.save() 


            #check if file formats are correct
            opath = os.path.join(settings.MEDIA_ROOT, str(job.pk),"Output")
            
            # 1. Motif input File
            #check = subprocess.Popen(['valid_Init',
            # str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))], 
            # stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            #out, err = check.communicate()
            out = "OK"  
            #out = out.decode('ascii')

            if out == "OK":
                job.status = "job ready to submit" 
                job.Motif_Initialization = "Custom File"
                job.mode = "Compare"
                job.save()
                runDiscovery.delay(job.pk)
                return render(request, 'job/submitted.html', {'pk': job.pk} )    
            else:
                job.delete()
                form = CompareForm()
                return render(request, 'job/motif_compare.html', {'form':form , 'type' : "Init", 'message' : out })
        else:
            form = CompareForm()
    else:
        form= CompareForm()

    return render(request, 'job/motif_compare.html', { 'form':form })

def OLD_compare_example(request):
    if request.method == "POST":
        form = ExampleCompareForm(request.POST, request.FILES)
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
                        print("create new anonymous user")
                        # create an anonymous user and log them in
                        username = ip
                        u = User(username=username, first_name='Anonymous', last_name='User')
                        u.set_unusable_password()
                        u.save()
                        job.user = u
                else:
                    print("we don't have an IP address for user")
            job.save() 

            # check if job has a name, if not use first 6 digits of job_id as job_name
            if job.job_name == None:
                # truncate job_id
                job_id_short = str(job.job_ID).split("-",1)
                job.job_name = job_id_short[0]
                job.save() 


            filename= 'example_data/stuff/oneMotif.peng'
            f = open(str(filename))
            out_filename = "oneMotif.meme"
            job.Input_Sequences.save(out_filename , File(f))
            f.close()
            job.save() 
            

            #check if file formats are correct
            opath = os.path.join(settings.MEDIA_ROOT, str(job.pk),"Output")
            
            # 1. Motif input File
            #check = subprocess.Popen(['valid_Init',
            # str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))], 
            # stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            #out, err = check.communicate()
            #out = out.decode('ascii')
            out = "OK"

            if out == "OK":
                job.status = "job ready to submit" 
                job.Motif_Initialization = "Custom File"
                job.mode = "Compare"
                job.save()
                runComparison.delay(job.pk)
                return render(request, 'job/submitted.html', {'pk': job.pk} )    
            else:
                job.delete()
                form = ExampleCompareForm()
                return render(request, 'job/compare_example.html', {'form':form , 'type' : "Init", 'message' : out })
        else:
            form = ExampleCompareForm()
    else:
        form= ExampleCompareForm()

    return render(request, 'job/compare_example.html', { 'form':form })


def OLD_data_discover(request):
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
                        print("create new anonymous user")
                        # create an anonymous user and log them in
                        username = ip
                        u = User(username=username, first_name='Anonymous', last_name='User')
                        u.set_unusable_password()
                        u.save()
                        job.user = u
                else:
                    print("we don't have an IP address for user")
            job.save() 

            # check if job has a name, if not use first 6 digits of job_id as job_name
            if job.job_name == None:
                # truncate job_id
                job_id_short = str(job.job_ID).split("-",1)
                job.job_name = job_id_short[0]
                job.save() 


            #check if file formats are correct
            opath = os.path.join(settings.MEDIA_ROOT, str(job.pk),"Output")
            
            # 1. Input sequence File
            check = subprocess.Popen(['valid_fasta',
             str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))], 
             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = check.communicate()
              
            out = out.decode('ascii')

            if out == "OK":
                job.status = "job ready to submit" 
                job.Motif_Initialization = "Custom File"
                job.mode = "Occurrence"
                job.save()
                print("OUT IS OK -> run the JOB")
                print("BG_model_File ->" + str(job.bgModel_File))
                runDiscovery.delay(job.pk)
                return render(request, 'job/submitted.html', {'pk': job.pk} )    
            else:
                job.delete()
                form = DiscoveryForm()
                return render(request, 'job/data_dicover.html', {'form':form , 'type' : "Fasta", 'message' : out })
        else:
            form = DiscoveryForm()
    else:
        form= DiscoveryForm()
    return render(request, 'job/data_discover.html', { 'form':form })

def OLD_data_discover_from_db(request, pk):
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
                        print("create new anonymous user")
                        # create an anonymous user and log them in
                        username = ip
                        u = User(username=username, first_name='Anonymous', last_name='User')
                        u.set_unusable_password()
                        u.save()
                        job.user = u
                else:
                    print("we don't have an IP address for user")
            job.save() 
            
            # upload motifInitFile
            filename= 'DB/' + str(db_entry.parent.base_dir) + '/Results/' + str(db_entry.result_location) + '/' + str(db_entry.result_location) + '_motif_1.ihbcp'
            f = open(str(filename))
            out_filename = str(db_entry.result_location) + ".ihbcp"
            job.Motif_InitFile.save(out_filename , File(f))
            f.close()
            job.Motif_Init_File_Format = "BaMM"
            job.save()
            
            # upload bgModelFile
            filename= 'DB/' + str(db_entry.parent.base_dir) + '/Results/' + str(db_entry.result_location) + '/' + str(db_entry.result_location) + '.hbcp'
            f = open(str(filename))
            out_filename = str(db_entry.result_location) + ".hbcp"
            job.bgModel_File.save(out_filename , File(f))
            f.close()
            job.save()
            
             # check if job has a name, if not use first 6 digits of job_id as job_name
            if job.job_name == None:
                # truncate job_id
                job_id_short = str(job.job_ID).split("-",1)
                job.job_name = job_id_short[0]
                job.save() 

            
            #check if file formats are correct
            opath = os.path.join(settings.MEDIA_ROOT, str(job.pk),"Output")
            
            # 1. Input sequence File
            check = subprocess.Popen(['valid_fasta',
             str(os.path.join(settings.MEDIA_ROOT, job.Input_Sequences.name))], 
             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            out, err = check.communicate()
              
            out = out.decode('ascii')

            if out == "OK":
                job.status = "job ready to submit" 
                job.Motif_Initialization = "Custom File"
                job.mode = "Occurrence"
                job.save()
                print("OUT IS OK -> run the JOB")
                runDiscovery.delay(job.pk)
                return render(request, 'job/submitted.html', {'pk': job.pk} )    
            else:
                job.delete()
                form = DiscoveryDBForm()
                return render(request, 'job/data_discoverDB.html', {'form':form , 'type' : "Fasta", 'message' : out })

        else:
            form = DiscoveryDBForm()
    else:
        form = DiscoveryDBForm()
    return render(request, 'job/data_discoverDB.html',{'form': form, 'pk':pk, 'db_entry':db_entry})

def OLD_result_detail(request, pk):
    print( 'entered result detail view')
    result = get_object_or_404(Job, pk=pk)
    print( 'result received')
    opath = os.path.join(settings.MEDIA_ROOT,str(result.pk),"Output")
    print('defined opath')
    print(opath)
    Output_filename, ending = os.path.splitext(os.path.basename(result.Input_Sequences.name))
    print('extracted output filename and ending')
    if result.status == 'Successfully finished':
        print("status is successfull")
        num_logos = range(1, (min(2,result.model_Order)+1))
        print('logo number calculated')
        if result.mode == 'Prediction':
            return render(request,'results/result_detail.html', {'result':result, 'opath':opath, 'Output_filename':Output_filename, 'num_logos':num_logos})

        if result.mode == 'Occurrence':
            print("RESULT.numMOTIFS=" + str(result.num_motifs))
            return redirect('test', pk)

    else:
        print('status not ready yet')
        command ="tail -20 /code/media/logs/" + pk + ".log"
        output = os.popen(command).read()
        return render(request,'results/result_status.html', {'result':result, 'opath':opath , 'output':output })


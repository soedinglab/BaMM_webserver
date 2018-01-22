import datetime
import subprocess
import os
from ipware.ip import get_ip

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.conf import settings

from bammmotif.peng.settings import file_path_peng, peng_meme_directory, FASTA_VALIDATION_SCRIPT, PENG_OUTPUT, MEME_PLOT_INPUT, FILTERPWM_OUTPUT_FILE
from webserver.settings import BAMM_INPUT
from bammmotif.models import JobInfo
from bammmotif.peng.settings import ALLOWED_JOBMODES, file_path_peng_meta
from bammmotif.utils import get_user
from bammmotif.utils.meme_reader import get_n_motifs
from bammmotif.peng.form import JobInfoForm

#def file_path_peng(job_id, filename):
#    path_to_job = os.path.join(settings.MEDIA_ROOT, str(job_id), 'Output')
#    if not os.path.exists(path_to_job):
#        os.makedirs(path_to_job)
#    return os.path.join(path_to_job, str(filename))

#def peng_meme_directory(job_id):
#    path_to_plots = os.path.join(settings.MEDIA_ROOT, str(job_id), 'Output')
#    if not os.path.exists(path_to_plots):
#        os.makedirs(path_to_plots)
#    return path_to_plots

def init_job(job_type):
    job = JobInfo.objects.create()
    job.created_at = datetime.datetime.now()
    job.status = "data uploaded"
    job.job_type = job_type
    if job.job_name is None:
        # truncate job_id
        job_id_short = str(job.job_id).split("-", 1)
        job.job_name = job_id_short[0]
    job.save()
    return job

def init_job_from_form(job_type, request):
    form = JobInfoForm(request.POST, request.FILES)
    job = form.save(commit=False)
    job.created_at = datetime.datetime.now()
    job.status = "data uploaded"
    job.job_type = job_type
    if job.job_name is None:
        # truncate job_id
        job_id_short = str(job.job_id).split("-", 1)
        job.job_name = job_id_short[0]
    job.save()
    return job


def create_bamm_job(job_type, request, form, peng_job):
    #job_info = init_job('bamm')
    job_info = init_job_from_form(job_type, request)
    job_info.user = get_user(request)
    # bamm_job = create_job_bamm(form, request, "bamm")
    # read in data and parameter
    bamm_job = form.save(commit=False)
    bamm_job.job_id = job_info
    # job.created_at = datetime.datetime.now()
    bamm_job.Input_Sequences = peng_job.fasta_file
    bamm_job.num_init_motifs = get_n_motifs(peng_job.job_id.job_id)
    # print(dir(peng_job.fasta_file))
    bamm_job.Motif_InitFile.name = os.path.join(settings.MEDIA_ROOT, str(bamm_job.job_id.job_id), PENG_OUTPUT, FILTERPWM_OUTPUT_FILE)
    bamm_job.Motif_Initialization = "Custom File"
    bamm_job.Motif_Init_File_Format = "PWM"
    bamm_job.peng = peng_job
    bamm_job.save()
    return bamm_job

def create_anonymuous_user(request):
    ip = get_ip(request)
    if ip is None:
        print("Anonymous user has no ip. User name is for now set to 0.")
        #TODO: Check that this is ok.
        return User(username="0", first_name="Anonymous", last_name="User")
    else:
        # check if anonymous user already exists
        anonymous_users = User.objects.filter(username=ip)
        if anonymous_users.exists():
            print("user already exists")
            return get_object_or_404(User, username=ip)
        print("create new anonymous user")
        # create an anonymous user and log them in
        username = ip
        user = User(username=username, first_name='Anonymous', last_name='User')
        user.set_unusable_password()
        user.save()
        return user


def create_job_meta(form, request, job_type, from_jobinfo_form=False):
    if from_jobinfo_form:
        job_info = init_job_from_form(job_type, request)
    else:
        job_info = init_job(job_type)
    job = form.save(commit=False)
    job.job_id = job_info
    # Invert Default boolean values beginning with "no"
    job.no_em = not job.no_em
    job.no_merging = not job.no_merging
    # Add correct path to files.
    job.meme_output = file_path_peng_meta(job.job_id, job.meme_output)
    job.json_output = file_path_peng_meta(job.job_id, job.json_output)
    if job.strand == 'on':
        job.strand = "BOTH"
    else:
        job.stand = "PLUS"
    if request.user.is_authenticated:
        print("user is authenticated")
        job.user = request.user
    else:
        print("user is not authenticated")
        job.user = create_anonymuous_user(request)
    print("JOB ID = ", str(job.pk))
    # check if job has a name, if not use first 6 digits of job_id as job_name
    print("UPLOAD COMPLETE: save job object")
    job.save()
    return job

def create_job(form, request):
    job = form.save(commit=False)
    job.created_at = datetime.datetime.now()
    job.status = "data uploaded"
    # Invert Default boolean values beginning with "no"
    # TODO: Find a better solution for this.
    job.no_em = not job.no_em
    job.no_merging = not job.no_merging
    # Add correct path to files.
    job.meme_output = file_path_peng(job.job_ID, job.meme_output)
    job.json_output = file_path_peng(job.job_ID, job.json_output)
    if job.strand == 'on':
        job.strand = "BOTH"
    else:
        job.stand = "PLUS"
    if request.user.is_authenticated:
        print("user is authenticated")
        job.user = request.user
    else:
        print("user is not authenticated")
        job.user = create_anonymuous_user(request)
    print("JOB ID = ", str(job.pk))
    # check if job has a name, if not use first 6 digits of job_id as job_name
    if job.job_name is None:
        # truncate job_id
        job_id_short = str(job.job_ID).split("-", 1)
        job.job_name = job_id_short[0]
    print("UPLOAD COMPLETE: save job object")
    job.save()
    return job


def validate_fasta(path):
    ret = subprocess.Popen([FASTA_VALIDATION_SCRIPT, path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    res, err = ret.communicate()
    if res.decode('ascii') == "OK":
        return err, True
    print(err)
    return err, False


def validate_input_data(job):
    print("VALIDATE_INPUT_DATA")
    success = "Validation succeeded!"
    print(settings.MEDIA_ROOT)
    print(job.fasta_file.name)
    msg_seq, valid_seq = validate_fasta(os.path.join(settings.MEDIA_ROOT, job.fasta_file.name))
    if not valid_seq:
        return msg_seq, False
    if job.bg_sequences.name is not None:
        msg_background, valid_background = validate_fasta(os.path.join(settings.MEDIA_ROOT, job.bg_sequences.name))
        if not valid_background:
            return msg_background, False
    return success, True

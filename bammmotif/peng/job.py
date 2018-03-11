import subprocess
import os
from os import path
from ipware.ip import get_ip

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .settings import (
    FASTA_VALIDATION_SCRIPT,
    PENG_OUTPUT,
    MEME_PLOT_INPUT,
    FILTERPWM_OUTPUT_FILE,
    MEME_OUTPUT_FILE
)

from .io import (
    get_peng_meme_output_in_bamm,
    peng_output_meme_file,
    get_motif_init_file,
)
from .utils import get_selected_motifs

from ..utils import (
    get_user,
    meme_count_motifs,
    get_job_output_folder,
    register_job_session,
)
from ..utils.meme_reader import get_n_motifs
from ..models import JobInfo
from ..forms import MetaJobNameForm


def init_job(job_type):
    job = JobInfo.objects.create()
    job.status = "data uploaded"
    job.job_type = job_type
    if job.job_name is None:
        # truncate job_id
        job_id_short = str(job.job_id).split("-", 1)
        job.job_name = job_id_short[0]
    job.save()
    return job


def init_job_from_form(job_type, request):
    form = MetaJobNameForm(request.POST, request.FILES)
    job = form.save(commit=False)
    job.status = "data uploaded"
    job.job_type = job_type
    if job.job_name is None:
        # truncate job_id
        job_id_short = str(job.job_id).split("-", 1)
        job.job_name = job_id_short[0]
    return job


def create_bamm_job(job_type, request, form, peng_job):
    job_info = init_job_from_form(job_type, request)
    job_info.user = get_user(request)
    job_info.job_type = 'bamm'
    job_pk = job_info.pk

    bamm_job = form.save(commit=False)
    bamm_job.meta_job = job_info
    bamm_job.Input_Sequences = peng_job.fasta_file
    bamm_job.num_init_motifs = len(get_selected_motifs(request.POST))
    bamm_job.Motif_InitFile.name = get_motif_init_file(str(bamm_job.pk))
    bamm_job.Motif_Initialization = "Custom File"
    bamm_job.Motif_Init_File_Format = "PWM"
    bamm_job.peng_job = peng_job

    with transaction.atomic():
        job_info.save()
        register_job_session(request, job_info)
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


def create_job(form, meta_job_form, request):
    meta_job = meta_job_form.save(commit=False)
    meta_job.job_type = 'peng'
    job_pk = meta_job.pk

    job = form.save(commit=False)
    # Add correct path to files.
    output_dir = get_job_output_folder(job_pk)
    job.meme_output = path.join(output_dir, job.meme_output)
    job.json_output = path.join(output_dir, job.json_output)

    if request.user.is_authenticated:
        job.user = request.user
    else:
        job.user = create_anonymuous_user(request)
    # check if job has a name, if not use first 6 digits of job_id as job_name
    if meta_job.job_name is None:
        # truncate job_id
        job_id_short = str(meta_job.pk).split("-", 1)
        meta_job.job_name = job_id_short[0]
    job.meta_job = meta_job
    return job


def validate_fasta(path):
    ret = subprocess.Popen([FASTA_VALIDATION_SCRIPT, path], stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    res, err = ret.communicate()
    if res.decode('ascii') == "OK":
        return err, True
    return err, False


def validate_input_data(job):
    fasta_file = path.join(settings.JOB_DIR_PREFIX, job.fasta_file.name)
    msg_seq, valid_seq = validate_fasta(fasta_file)
    if not valid_seq:
        return msg_seq, False
    if job.bg_sequences.name is not None:
        bg_file = path.join(settings.JOB_DIR_PREFIX, job.bg_sequences.name)
        msg_background, valid_background = validate_fasta(bg_file)
        if not valid_background:
            return msg_background, False
    return 'Validation Successful', True

import sys
import os
import collections
from os import path
from os.path import basename
import traceback
import subprocess
from shutil import copyfile
import re
from collections import OrderedDict

from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.files import File
from django.utils import timezone
from ipware.ip import get_ip
from ..models import (
    JobInfo, Motifs, ChIPseq, DbMatch
)

import logging
logger = logging.getLogger(__name__)


class JobSaveManager:

    def __init__(self, job, success_status='Success', error_status='Error'):
        self.error_status = error_status
        self.success_status = success_status
        self.job = job

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, tb):
        job = self.job
        if error_type is not None:
            job.meta_job.status = self.error_status
            self.had_exception = True
            traceback.print_exception(error_type, error, tb, file=sys.stdout)
            print(timezone.now(), "\t | WARNING: \t %s " % job.meta_job.status)
        else:
            job.meta_job.status = self.success_status
            self.had_exception = False
            print(timezone.now(), "\t | END: \t %s " % job.meta_job.status)
        job.save()


class CommandFailureException(Exception):
    pass


def run_command(command, enforce_exit_zero=True):

    if isinstance(command, str):
        command_str = command
    elif isinstance(command, collections.Iterable):
        command_str = ' '.join(command)
    logger.debug("executing: %s", command_str)

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    while True:
        nextline = process.stdout.readline()
        if nextline == b'' and process.poll() is not None:
            break
        print(nextline.decode('utf-8'), file=sys.stdout, end='')
        sys.stdout.flush()
    process.wait()

    if enforce_exit_zero:
        if process.returncode != 0:
            raise CommandFailureException(command_str)

    return process.returncode


def get_user(request):
    # assign user to new job instance 
    # login is currently unabled
    #if request.user.is_authenticated():
    #    return request.user
    #else:
    ip = get_ip(request)
    if ip is not None:
        # check if anonymous user already exists
        anonymous_users = User.objects.filter(username=ip)
        if anonymous_users.exists():
            return get_object_or_404(User, username=ip)
        else:
            # create an anonymous user and log them in
            new_u = User(username=ip, first_name='Anonymous',
                         last_name='User')
            new_u.set_unusable_password()
            new_u.save()
            return new_u
    else:
        print("NO USER SETABLE")


def set_job_name(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    # truncate job_id
    job_id_short = str(job.job_ID).split("-", 1)
    job.job_name = job_id_short[0]
    job.save()


def add_peng_output(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    out_filename = settings.PENG_INIT
    infile = path.join(get_job_input_folder(job_pk), settings.PENG_OUT)
    with open(infile) as fh:
        job.Motif_InitFile.save(out_filename, File(fh))
    job.Motif_Initialization = 'PEnGmotif'
    job.Motif_Init_File_Format = 'PWM'
    job.save()


def upload_db_input(job_pk, db_pk):
    job = get_object_or_404(Job, pk=job_pk)
    db_entry = get_object_or_404(ChIPseq, pk=db_pk)
    db_dir = path.join(settings.BASE_DIR + settings.DB_ROOT + '/' + db_entry.parent.base_dir + '/Results/' + db_entry.result_location)
    # upload motifInitFile
    f = db_dir + '/' + str(db_entry.result_location) + '_motif_1.ihbcp'
    out_f = str(db_entry.result_location) + ".ihbcp"
    with open(f) as fh:
        job.Motif_InitFile.save(out_f, File(fh))
    job.Motif_Initialization = 'CustomFile'
    job.Motif_Init_File_Format = "BaMM"

    # upload bgModelFile
    f = db_dir + '/' + str(db_entry.result_location) + '.hbcp'
    out_f = str(db_entry.result_location) + ".hbcp"
    with open(f) as fh:
        job.bgModel_File.save(out_f, File(fh))

    # adjust model order
    job.model_Order = db_entry.parent.modelorder
    job.background_Order = db_entry.parent.bgmodelorder
    job.save()


def initialize_motifs(job_pk, off, mode):
    job = get_object_or_404(Job, pk=job_pk)
    job.num_motifs = (len(os.listdir(
                           get_job_output_folder(job_pk))) - off)/mode
    job.save()
    for motif in range(1, (int(job.num_motifs) + 1)):
        motif_obj = Motifs(parent_job=job, job_rank=motif)
        motif_obj.save()

def initialize_motifs_compare(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        outname = basename(os.path.splitext(job.Motif_InitFile.name)[0])
    else:
        outname = basename(os.path.splitext(job.Input_Sequences.name)[0])
    fname = str(get_job_output_folder(job_pk)) + "/" + outname + ".iupac"
    with open(fname) as f:
        for i, l in enumerate(f):
            pass   
    job.num_motifs = i+1
    job.save()
    for motif in range(1, (int(job.num_motifs) + 1)):
        motif_obj = Motifs(parent_job=job, job_rank=motif)
        motif_obj.save()


def add_motif_evaluation(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    motifs = Motifs.objects.filter(parent_job=job)

    file_basename = basename(job.Input_Sequences.name)
    prefix, _ = path.splitext(file_basename)
    benchmark_file = path.join(get_job_output_folder(job_pk), prefix + ".bmscore")

    with open(benchmark_file) as bm_handle:
        next(bm_handle)  # skip header
        for line in bm_handle:
            tokens = line.split()
            motif_obj = motifs.filter(job_rank=tokens[1])[0]
            motif_obj.auc = tokens[2]
            motif_obj.occurrence = tokens[5]
            motif_obj.save()


def transfer_motif(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    make_job_output_folder(job_pk)
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        outname = basename(os.path.splitext(job.Motif_InitFile.name)[0])
    else:
        outname = basename(os.path.splitext(job.Input_Sequences.name)[0])
    offs = 1

    src = get_job_input_folder(job_pk) + '/' + basename(job.Motif_InitFile.name)
    input_ending = os.path.splitext(job.Motif_InitFile.name)[1]
    
    if job.Motif_Init_File_Format == 'PWM':
        dest = get_job_output_folder(job_pk) + '/' + outname + ".meme"
        copyfile(src, dest)
        
    if job.Motif_Init_File_Format == 'BaMM':
        dest = get_job_output_folder(job_pk) + '/' + outname + input_ending
        copyfile(src, dest)
        src = get_job_input_folder(job_pk) + '/' + basename(job.bgModel_File.name)
        dest = get_job_output_folder(job_pk) + '/' + outname + os.path.splitext(job.bgModel_File.name)[1]
        copyfile(src, dest)
        offs = 2
    
    return offs

def valid_uuid(uuid):
    regex = re.compile('^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}\Z', re.I)
    match = regex.match(uuid)
    return bool(match)


def meme_count_motifs(meme_file):
    n_motifs = 0
    with open(meme_file) as handle:
        for line in handle:
            if line.startswith('MOTIF'):
                n_motifs += 1
    return n_motifs


job_dir_storage = FileSystemStorage(location=settings.JOB_DIR)


def job_upload_to_input(job, filename):
    return path.join(str(job.meta_job.pk), 'Input', filename)

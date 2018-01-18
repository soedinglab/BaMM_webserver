from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.files import File
from ipware.ip import get_ip
from ..models import (
    ChIPseq, Bamm, JobInfo, Motifs_new, DbMatch_new
)
import sys
import os
from os import path
from os.path import basename
import datetime
import traceback
import subprocess
from shutil import copyfile
import re


def get_result_folder(job_id):
    return path.join(settings.JOB_DIR_PREFIX, str(job_id), 'Output')


def get_job_folder(job_id):
    return path.join(settings.MEDIA_ROOT, settings.JOB_DIR_PREFIX, str(job_id))


def make_job_folder(job_id):
    job_folder = get_job_folder(job_id)
    if not path.isdir(job_folder):
        os.makedirs(job_folder)
    return job_folder


def make_job_output_folder(job_id):
    job_output_folder = get_job_output_folder(job_id)
    if not path.isdir(job_output_folder):
        os.makedirs(job_output_folder)


def get_job_output_folder(job_id):
    return path.join(get_job_folder(job_id), 'Output')


def get_job_input_folder(job_id):
    return path.join(get_job_folder(job_id), 'Input')


def get_log_file(job_id):
    return path.join(get_job_folder(job_id), 'job.log')


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
            job.status = self.error_status
            self.had_exception = True
            traceback.print_exception(error_type, error, tb, file=sys.stdout)
            print(datetime.datetime.now(), "\t | WARNING: \t %s " % job.status)
        else:
            job.status = self.success_status
            self.had_exception = False
            print(datetime.datetime.now(), "\t | END: \t %s " % job.status)
        job.save()
        return True


def run_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    while True:
        nextline = process.stdout.readline()
        if nextline == b'' and process.poll() is not None:
            break
        print(nextline.decode('utf-8'), file=sys.stdout, end='')
        sys.stdout.flush()
    process.wait()
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
    job = get_object_or_404(JobInfo, pk=job_pk)
    # truncate job_id
    job_id_short = str(job.job_id).split("-", 1)
    job.job_name = job_id_short[0]
    job.save()


def upload_example_fasta(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    out_filename = "ExampleData.fasta"
    with open(settings.EXAMPLE_FASTA) as fh:
        job.Input_Sequences.save(out_filename, File(fh))
        job.save()


def upload_example_motif(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    out_filename = "ExampleMotif.meme"
    with open(settings.EXAMPLE_MOTIF) as fh:
        job.Motif_InitFile.save(out_filename, File(fh))
    job.Motif_Initialization = 'CustomFile'
    job.Motif_Init_File_Format = 'PWM'
    job.save()


def add_peng_output(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    out_filename = settings.PENG_INIT
    infile = path.join(get_job_input_folder(job_pk), settings.PENG_OUT)
    with open(infile) as fh:
        job.Motif_InitFile.save(out_filename, File(fh))
    job.Motif_Initialization = 'PEnGmotif'
    job.Motif_Init_File_Format = 'PWM'
    job.save()


def upload_db_input(job_pk, db_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
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
    job = get_object_or_404(Bamm, pk=job_pk)
    job.num_motifs = (len(os.listdir(
                           get_job_output_folder(job_pk))) - off)/mode
    job.save()
    for motif in range(1, (int(job.num_motifs) + 1)):
        motif_obj = Motifs_new(parent_job=job, job_rank=motif)
        motif_obj.save()

def initialize_motifs_compare(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
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
        motif_obj = Motifs_new(parent_job=job, job_rank=motif)
        motif_obj.save()

def add_motif_evaluation(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    motifs = Motifs_new.objects.filter(parent_job=job)
    filename = str(get_job_output_folder(job_pk)) + "/" + str(basename(os.path.splitext(job.Input_Sequences.name)[0])) + ".bmscore"
    with open(filename) as fh:
        next(fh)
        for line in fh:
            tokens = line.split()
            motif_obj = motifs.filter(job_rank=tokens[1])[0]
            motif_obj.auc = tokens[2]
            motif_obj.occurrence = tokens[5]
            motif_obj.save()


def add_motif_motif_matches(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    motifs = Motifs_new.objects.filter(parent_job=job)
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        outname = basename(os.path.splitext(job.Motif_InitFile.name)[0])
    else:
        outname = basename(os.path.splitext(job.Input_Sequences.name)[0])
    filename = str(get_job_output_folder(job_pk)) + "/" + outname + ".mmcomp"
    with open(filename) as fh:
        for line in fh:
            tokens = line.split()
            if len(tokens) > 0:
                if tokens[1] != 'matches!':
                    motif_query = motifs.filter(job_rank=tokens[1])[0]
                    motif_target = get_object_or_404(ChIPseq, filename=tokens[2])
                    # create relationship
                    rel_obj = DbMatch_new(
                        motif=motif_query,
                        db_entry=motif_target,
                        p_value=tokens[3],
                        e_value=tokens[4],
                        score=tokens[5],
                        overlap_len=tokens[6]
                    )
                    rel_obj.save()


def add_motif_iupac(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    motifs = Motifs_new.objects.filter(parent_job=job)
    if basename(os.path.splitext(job.Input_Sequences.name)[0]) == '':
        outname = basename(os.path.splitext(job.Motif_InitFile.name)[0])
    else:
        outname = basename(os.path.splitext(job.Input_Sequences.name)[0])
    filename = str(get_job_output_folder(job_pk)) + "/" + outname + ".iupac"
    with open(filename) as fh:
        for line in fh:
            tokens = line.split()
            motif_obj = motifs.filter(job_rank=tokens[1])[0]
            motif_obj.iupac = tokens[2]
            motif_obj.length = tokens[3]
            motif_obj.save()


def transfer_motif(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
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


def get_model_order(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    filename = get_job_input_folder(job_pk) + '/' + basename(job.Motif_InitFile.name)
    order = -1
    with open(filename) as fh:
        for line in fh:
            tokens = line.split()
            if len(tokens) == 0:
                return (order)
            else:
                order = order + 1
    return order


def get_bg_model_order(job_pk):
    job = get_object_or_404(Bamm, pk=job_pk)
    filename = get_job_input_folder(job_pk) + '/' + basename(job.bgModel_File.name)
    order = -1
    with open(filename) as fh:
        for line in fh:
            tokens = line.split()
            order = tokens[3]
            break
    return order

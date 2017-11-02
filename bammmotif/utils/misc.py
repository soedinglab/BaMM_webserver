from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.files import File
from ipware.ip import get_ip
from ..models import (
    Job, Motifs, ChIPseq, DbMatch
)
import sys
import os
from os import path
from os.path import basename
import datetime
import traceback
import subprocess
from shutil import copyfile


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
    if request.user.is_authenticated():
        return request.user
    else:
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


def upload_example_fasta(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    out_filename = "ExampleData.fasta"
    with open(settings.EXAMPLE_FASTA) as fh:
        job.Input_Sequences.save(out_filename, File(fh))
        job.save()


def upload_example_motif(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    out_filename = "ExampleMotif.meme"
    with open(settings.EXAMPLE_MOTIF) as fh:
        job.Motif_InitFile.save(out_filename, File(fh))
    job.Motif_Initialization = 'Custom File'
    job.Motif_Init_File_Format = 'PWM'
    job.model_Order = 0
    job.save()


def upload_db_input(job_pk, db_pk):
    job = get_object_or_404(Job, pk=job_pk)
    db_entry = get_object_or_404(ChIPseq, pk=db_pk)
    db_dir = path.join(settings.DB_ROOT + '/' + db_entry.parent.base_dir + '/Results/' + db_entry.result_location)
    # upload motifInitFile
    f = db_dir + '/' + str(db_entry.result_location) + '_motif_1.ihbcp'
    out_f = str(db_entry.result_location) + ".ihbcp"
    with open(f) as fh:
        job.Motif_InitFile.save(out_f, File(fh))
    job.Motif_Initialization = 'Custom File'
    job.Motif_Init_File_Format = "BaMM"

    # upload bgModelFile
    f = db_dir + '/' + str(db_entry.result_location) + '.hbcp'
    out_f = str(db_entry.result_location) + ".hbcp"
    with open(f) as fh:
        job.bgModel_File.save(out_f, File(fh))
    job.save()

    # adjust model order
    job.model_Order = db_entry.parent.modelorder
    job.background_Order = db_entry.parent.bgmodelorder


def initialize_motifs(job_pk, off, mode):
    job = get_object_or_404(Job, pk=job_pk)
    job.num_motifs = (len(os.listdir(
                           get_job_output_folder(job_pk))) - off)/mode
    job.save()
    for motif in range(1, (int(job.num_motifs) + 1)):
        motif_obj = Motifs(parent_job=job, job_rank=motif)
        motif_obj.save()


def add_motif_evaluation(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    motifs = Motifs.objects.filter(parent_job=job)
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
    job = get_object_or_404(Job, pk=job_pk)
    motifs = Motifs.objects.filter(parent_job=job)
    filename = str(get_job_output_folder(job_pk)) + "/" + str(basename(os.path.splitext(job.Input_Sequences.name)[0])) + ".mmcomp"
    with open(filename) as fh:
        for line in fh:
            tokens = line.split()
            motif_query = motifs.filter(job_rank=tokens[1])[0]
            motif_target = get_object_or_404(ChIPseq, filename=tokens[2])
            # create relationship
            rel_obj = DbMatch(
                motif=motif_query,
                db_entry=motif_target,
                p_value=tokens[3],
                e_value=tokens[4],
                score=tokens[5],
                overlap_len=tokens[6]
            )
            rel_obj.save()


def add_motif_iupac(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    motifs = Motifs.objects.filter(parent_job=job)
    filename = str(get_job_output_folder(job_pk)) + "/" + str(basename(os.path.splitext(job.Input_Sequences.name)[0])) + ".iupac"
    with open(filename) as fh:
        for line in fh:
            tokens = line.split()
            motif_obj = motifs.filter(job_rank=tokens[1])[0]
            motif_obj.iupac = tokens[2]
            motif_obj.length = tokens[3]
            motif_obj.save()


def transfer_motif(job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    make_job_output_folder(job_pk)

    src = get_job_input_folder(job_pk) + '/' + basename(job.Motif_InitFile.name)
    input_ending = os.path.splitext(job.Motif_InitFile.name)[1]
    if job.Input_Sequences is None:
        dest = get_job_output_folder(job_pk) + '/' + basename(job.Motif_InitFile.name)
        # add this file also as Input_Sequences File to generate MMcompare command
        with open(src) as fh:
            job.Input_Sequences.save(basename(job.Motif_InitFile.name), File(fh))
            job.save()
    else:
        dest = get_job_output_folder(job_pk) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + '_motif_1' + input_ending
    copyfile(src, dest)
    offs = 1
    if input_ending == '.ihbcp':
        src = get_job_input_folder(job_pk) + '/' + basename(job.bgModel_File.name)
        if job.Input_Sequences is None:
            dest = get_job_output_folder(job_pk) + '/' + basename(job.bgModel_File.name)
        else:
            dest = get_job_output_folder(job_pk) + '/' + basename(os.path.splitext(job.Input_Sequences.name)[0]) + os.path.splitext(job.bgModel_File.name)[1]
        copyfile(src, dest)
        offs = 2
    return offs

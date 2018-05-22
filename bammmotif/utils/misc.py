import sys
import os
from os import path
from os.path import basename
import traceback
import subprocess
from shutil import copyfile
import re
from tempfile import NamedTemporaryFile

from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.files import File
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.fields import FieldDoesNotExist
from ipware.ip import get_ip

from celery.exceptions import SoftTimeLimitExceeded

from ..models import (
    Motifs,
    ChIPseq,
    JobSession,
)

from ..utils.input_validation import (
    validate_fasta_file,
    validate_bamm_file,
    validate_meme_file,
    validate_bamm_bg_file,
    validate_generic_meme,
    MEMEValidationError,
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

        if error_type is SoftTimeLimitExceeded:
            job.meta_job.status = 'Killed'
            self.had_exception = True
            print(timezone.now(), "\t | WARNING: \t Exceeded time limit.")
            logger.warn('Job %s exceeded the time limit and was killed.', job.meta_job.pk)

            job.meta_job.save()
            job.save()

            # swallow the exception
            return True

        elif error_type is not None:
            job.meta_job.status = self.error_status
            self.had_exception = True
            logger.exception(error)
            traceback.print_exception(error_type, error, tb, file=sys.stdout)
            print(timezone.now(), "\t | WARNING: \t %s " % job.meta_job.status)

            # swallow the exception
            return True

        else:
            job.meta_job.status = self.success_status
            self.had_exception = False
            print(timezone.now(), "\t | END: \t %s " % job.meta_job.status)
        job.meta_job.save()
        job.save()


class CommandFailureException(Exception):
    pass


url_prefix = {
    'peng': 'seed_results',
    'refine': 'refine_results',
    'bammscan': 'scan_results',
    'mmcompare': 'compare_results',
    'denovo': 'denovo_results',
}


def run_command(command, enforce_exit_zero=True):

    command = [str(s) for s in command]

    command_str = ' '.join('%r' % s for s in command)
    logger.debug("executing: %s", command_str)

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
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


def set_job_name_if_unset(job):
    if job.job_name is None:
        # truncate job_id
        job_id_short = str(job).split("-", maxsplit=1)
        job.job_name = job_id_short[0]


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


def is_fasta(name):
    return name.endswith('.fa') or name.endswith('.fasta')


filename_relative_to_job_dir = job_upload_to_input


def get_session_key(request):
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def register_job_session(request, meta_job):
    session_key = get_session_key(request)
    session_record = JobSession(session_key=session_key, job=meta_job)
    session_record.save()


# adapted from: https://stackoverflow.com/a/35321718/2272172
def file_size_validator(value):
    if value.size > settings.MAX_UPLOAD_FILE_SIZE:
        raise ValidationError('File size exceeds upload limits.')


def check_motif_input(job, form, request):
    is_valid = True
    if job.Motif_Init_File_Format == 'MEME':
        success, msg = check_meme_input(job, form, request.FILES)
        if not success:
            form.add_error('Motif_InitFile', msg)
            is_valid = False
    elif job.Motif_Init_File_Format == 'BaMM':
        if not validate_bamm_file(job.full_motif_file_path):
            form.add_error('Motif_InitFile', 'Does not seem to be in BaMM format.')
            is_valid = False
        if not job.bgModel_File:
            form.add_error('bgModel_File', 'This field is required.')
            is_valid = False
        elif not validate_bamm_bg_file(job.full_motif_bg_file_path):
            form.add_error('bgModel_File', 'Does not seem to be a BaMM '
                                           'background model.')
            is_valid = False

    return is_valid


def check_fasta_input(job, form, rq_files):
    try:
        job._meta.get_field('Input_Sequences')
        fasta_field = 'Input_Sequences'
    except FieldDoesNotExist:
        fasta_field = 'fasta_file'

    with NamedTemporaryFile('wb+') as tmp_file:
        for chunk in rq_files[fasta_field].chunks():
            tmp_file.write(chunk)
        tmp_file.flush()
        success, msg = validate_fasta_file(tmp_file.name)

    if not success:
        form.add_error(fasta_field, msg)
        return False
    return True


def check_meme_input(job, form, rq_files):
    motif_field = 'Motif_InitFile'

    with NamedTemporaryFile('wb+') as tmp_file:
        for chunk in rq_files[motif_field].chunks():
            tmp_file.write(chunk)
        tmp_file.flush()

        try:
            validate_generic_meme(tmp_file.name)
        except MEMEValidationError as ex:
            return False, str(ex)
        except ValueError as unknown_err:
            logger.exception(unknown_err)
            return False, 'generic parsing problem of the MEME file'

        return True, 'Success'

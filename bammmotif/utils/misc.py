import sys
from os import path
import traceback
import subprocess
import re
from tempfile import NamedTemporaryFile
import signal

from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models.fields import FieldDoesNotExist
from ipware.ip import get_ip

from celery.exceptions import SoftTimeLimitExceeded

from ..models import (
    JobSession,
)

from ..utils.input_validation import (
    validate_fasta_file,
    validate_bamm_file,
    validate_generic_meme,
    FileFormatValidationError,
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

        swallow_exception = False

        if error_type is SoftTimeLimitExceeded:
            job.meta_job.status = 'Killed'
            self.had_exception = True
            print(timezone.now(), "\t | WARNING: \t Exceeded time limit.")
            logger.warn('Job %s exceeded the time limit and was killed.', job.meta_job.pk)
            swallow_exception = True

        elif error_type is not None:
            job.meta_job.status = self.error_status
            self.had_exception = True
            logger.exception(error)
            traceback.print_exception(error_type, error, tb, file=sys.stdout)
            print(timezone.now(), "\t | WARNING: \t %s " % job.meta_job.status)
            swallow_exception = True

        else:
            job.meta_job.status = self.success_status
            self.had_exception = False
            print(timezone.now(), "\t | END: \t %s " % job.meta_job.status)

        job.meta_job.save()
        job.save()
        return swallow_exception


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
        logger.error('we should not have ended here.')


def set_job_name_if_unset(job):
    if job.job_name is None:
        # truncate job_id
        job_id_short = str(job).split("-", maxsplit=1)
        job.job_name = job_id_short[0]


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
        success, msg = check_bamm_input(job, form, request.FILES, homogeneous=False)
        if not success:
            form.add_error('Motif_InitFile', 'Problem parsing the BaMM format - %s' % msg)
            is_valid = False

        if not job.bgModel_File:
            form.add_error('bgModel_File', 'This field is required.')
            is_valid = False
        else:
            success, msg = check_bamm_input(job, form, request.FILES, homogeneous=True)
            if not success:
                form.add_error('bgModel_File', 'Problem parsing the BaMM format - %s' % msg)
                is_valid = False

    return is_valid


def check_fasta_input(job, form, rq_files, bg_seqs=False):

    if bg_seqs:
        fasta_field = get_seq_model_field(job, 'Background_Sequences', 'bg_sequences')
    else:
        fasta_field = get_seq_model_field(job, 'Input_Sequences', 'fasta_file')

    with NamedTemporaryFile('wb+') as tmp_file:
        for chunk in rq_files[fasta_field].chunks():
            tmp_file.write(chunk)
        tmp_file.flush()
        success, msg = validate_fasta_file(tmp_file.name)

    if not success:
        form.add_error(fasta_field, msg)
        return False
    return True


def get_seq_model_field(job, option1, option2):
    try:
        job._meta.get_field(option1)
        field_name = option1
    except FieldDoesNotExist:
        field_name = option2
    return field_name
    


def check_meme_input(job, form, rq_files):
    motif_field = 'Motif_InitFile'

    with NamedTemporaryFile('wb+') as tmp_file:
        for chunk in rq_files[motif_field].chunks():
            tmp_file.write(chunk)
        tmp_file.flush()

        try:
            validate_generic_meme(tmp_file.name)
        except FileFormatValidationError as ex:
            return False, str(ex)
        except ValueError as unknown_err:
            logger.exception(unknown_err)
            return False, 'generic parsing problem of the MEME file'

        return True, 'Success'


def check_bamm_input(job, form, rq_files, homogeneous=False):
    if not homogeneous:
        motif_field = 'Motif_InitFile'
    else:
        motif_field = 'bgModel_File'

    with NamedTemporaryFile('wb+') as tmp_file:
        for chunk in rq_files[motif_field].chunks():
            tmp_file.write(chunk)
        tmp_file.flush()

        try:
            validate_bamm_file(tmp_file.name, homogeneous)
        except FileFormatValidationError as ex:
            return False, str(ex)
        except ValueError as unknown_err:
            logger.exception(unknown_err)
            return False, 'generic parsing problem of the BaMM file'

        return True, 'Success'

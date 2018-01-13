import datetime
import subprocess
import os
from ipware.ip import get_ip
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.conf import settings


def file_path_peng(job_id, filename):
    path_to_job = os.path.join(settings.MEDIA_ROOT, str(job_id), 'Output')
    if not os.path.exists(path_to_job):
        os.makedirs(path_to_job)
    return os.path.join(path_to_job, str(filename))

def create_anonymuous_user(request):
    ip = get_ip(request)
    if ip is None:
        print("Anonymous user has no ip. User name is for now set to 0.")
        #TODO: Check that this is ok.
        return User(username="0", first_name="Anonymous", last_name="User")
    else:
        # check if anonymous user already exists
        anonymous_users = User.objects.filter(username=ip)
        type(anonymous_users)
        print("ANONYMOUS: ", anonymous_users)
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
    if request.user.is_authenticated():
        print("user is authenticated")
        job.user = request.user
    else:
        print("user is not authenticated")
        job.user = create_anonymuous_user(request)
    pass
    print("JOB ID = ", str(job.pk))

    # check if job has a name, if not use first 6 digits of job_id as job_name
    if job.job_name is None:
        # truncate job_id
        job_id_short = str(job.job_ID).split("-", 1)
        job.job_name = job_id_short[0]
    print("UPLOAD COMPLETE: save job object")
    job.save()
    print(job.__dict__)
    return job


def validate_fasta(path):
    fasta_script = '/code/bammmotif/static/scripts/valid_fasta'
    ret = subprocess.Popen([fasta_script, path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    res, err = ret.communicate()
    if res.decode('ascii') == "OK":
        return err, True
    print(err)
    return err, False


def validate_input_data(job):
    print("VALIDATE_INPUT_DATA")
    success = "Validation succeeded!"
    msg_seq, valid_seq = validate_fasta(os.path.join(settings.MEDIA_ROOT, job.fasta_file.name))
    if not valid_seq:
        return msg_seq, False
    if job.bg_sequences.name is not None:
        msg_background, valid_background = validate_fasta(os.path.join(settings.MEDIA_ROOT, job.bg_sequences.name))
        if not valid_background:
            return msg_background, False
    return success, True

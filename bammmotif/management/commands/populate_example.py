from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db import transaction
from bammmotif.peng.tasks import peng_seeding_pipeline
from bammmotif.bamm.tasks import bamm_refinement_pipeline
from bammmotif.bammscan.tasks import bamm_scan_pipeline
from bammmotif.mmcompare.tasks import mmcompare_pipeline
from bammmotif.models import JobInfo, PengJob, BaMMJob, BaMMScanJob, MMcompareJob
import datetime
import time
#from ...utils import (
#    upload_example_fasta,
#    upload_example_motif
#)
from bammmotif.bamm.utils import (
    upload_example_fasta,
    upload_example_motif,
)
from bammmotif.utils.misc import is_fasta
from webserver.settings import EXAMPLE_DIR

import uuid
import os

INITIAL_EXAMPLE_UUID = 0

def example_not_in_db(example_file):
    example_user = get_object_or_404(User, username='Example_User')
    example_jobs = JobInfo.objects.filter(user=example_user)
    jobs = example_jobs.job_id_set()
    for job in jobs:
        if job.meta_job.job_type == "peng":
            if example_file == job.fasta_file:
                return True
        elif job.meta_job.job_type == "bamm":
            if example_file == job.Input_Sequences:
                return True
    return False

def new_example_job_info(next_id, job_type):
    example_user = get_object_or_404(User, username='Example_User')
    job_info = JobInfo(
        job_id=uuid.UUID(int=next_id),
        job_name='Example Data',
        created_at=datetime.datetime.now(),
        mode='Prediction',
        complete=False,
        job_type=job_type,
        user=example_user,
    )
    return job_info, next_id + 1


def add_example_to_db(example_file, next_id):
    #First peng job
    job_info, next_id = new_example_job_info(next_id, 'peng')
    peng = PengJob(
        meta_job=job_info,
        fasta_file=example_file,
    )
    with transaction.atomic():
        job_info.save()
        peng.save()
    peng_seeding_pipeline.delay(peng.meta_job.pk)
    while not job_info.complete:
        time.sleep(5)
    #Now do bamm job
    job_info, next_id = new_example_job_info(next_id, 'bamm')
    bamm_job = BaMMJob(
        meta_job=job_info,
        Input_Sequences=example_file,
        MMcompare=False,
        score_Seqset=False,
        peng_job=peng,
    )
    with transaction.atomic():
        job_info.save()
        bamm_job.save()
    bamm_refinement_pipeline.delay(bamm_job.meta_job.pk)
    while not job_info.complete:
        time.sleep(5)
    #Now bammscan
    job_info, next_id = new_example_job_info(next_id, 'bammscan')
    bamm_scan_job = BaMMScanJob(
        meta_job=job_info,
        Input_Sequences=example_file,
        MMcompare=False,
    )
    with transaction.atomic():
        job_info.save()
        bamm_scan_job.save()
    bamm_scan_pipeline.delay(bamm_scan_job.meta_job.pk)
    while not job_info.complete:
        time.sleep(5)
    #Now MMCompare
    job_info, next_id = new_example_job_info(next_id, 'mmcompare')
    mmcompare_job = MMcompareJob(
        meta_job=job_info,
        # Fill in missing data
    )
    with transaction.atomic():
        job_info.save()
        mmcompare_job.save()
    mmcompare_pipeline.delay(mmcompare_job.meta_job.pk)
    return next_id



class Command(BaseCommand):
    def handle(self, *args, **options):

       # # create parent job
       # new_entry = Job(
       #     job_ID='b43a98d7-cf12-4c9c-8259-53d13c47a0d9',
       #     job_name='Example Data ',
       #     created_at=datetime.datetime.now(),
       #     mode='Prediction',
       #     Motif_Initialization='Custom File',
       #     Motif_Init_File_Format='PWM',
       #     num_init_motifs=3,
       #     model_Order=4,
       #     extend=4,
       #     num_motifs=3,
       #     complete=True
       #     )
       # u = User(username='Example_User', first_name='User', last_name='Example')
       # u.set_unusable_password()
       # u.save()
       # new_entry.user = u

       # new_entry.save()

       # upload_example_fasta(new_entry.job_ID)
       # upload_example_motif(new_entry.job_ID)

       # run_bamm.delay(new_entry.job_ID)

        # Check if user exists in db
        if not User.objects.filter(username='Example_User').exists():
            u = User(username='Example_User', first_name='User', last_name='Example')
            u.set_unusable_password()
            u.save()
        example_list = [os.path.join(EXAMPLE_DIR, x) for x in os.listdir(EXAMPLE_DIR) if is_fasta(x)]
        next_id = INITIAL_EXAMPLE_UUID + JobInfo.objects.filter(user_username='Example_User')
        for example in example_list:
            if example_not_in_db(example):
                next_id = add_example_to_db(example, next_id)

#
#        # create parent job
#        new_job_info = JobInfo(
#            job_id=uuid.UUID('b43a98d7-cf12-4c9c-8259-53d13c47a0d9'),
#            job_name='Example Data ',
#            created_at=datetime.datetime.now(),
#            mode='Prediction',
#            #Motif_Initialization='Custom File',
#            #Motif_Init_File_Format='PWM',
#            #num_init_motifs=3,
#            #model_Order=4,
#            #extend=4,
#            #num_motifs=3,
#            complete=True,
#            job_type='bamm'
#
#
#        )
#        u = User(username='Example_User', first_name='User', last_name='Example')
#        u.set_unusable_password()
#        u.save()
#        new_job_info.user = u
#
#        new_job_info.save()
#        new_bamm = Bamm(
#            job_id=new_job_info,
#            Motif_Initialization='Custom File',
#            Motif_Init_File_Format='PWM',
#            num_init_motifs=3,
#            model_Order=4,
#            extend=4,
#            num_motifs=3,
#        )
#        new_bamm.save()
#
#
#        upload_example_fasta(new_bamm.job_id)
#        upload_example_motif(new_bamm.job_id)
#
#        run_bamm.delay(new_bamm.job_id.job_id)

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from bammmotif.models import Job, Bamm, JobInfo
from bammmotif.bamm.tasks import run_bamm
import datetime
#from ...utils import (
#    upload_example_fasta,
#    upload_example_motif
#)
from bammmotif.bamm.utils import (
    upload_example_fasta,
    upload_example_motif
)

import uuid


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

        # create parent job
        new_job_info = JobInfo(
            job_id=uuid.UUID('b43a98d7-cf12-4c9c-8259-53d13c47a0d9'),
            job_name='Example Data ',
            created_at=datetime.datetime.now(),
            mode='Prediction',
            #Motif_Initialization='Custom File',
            #Motif_Init_File_Format='PWM',
            #num_init_motifs=3,
            #model_Order=4,
            #extend=4,
            #num_motifs=3,
            complete=True,
            job_type='bamm'


        )
        u = User(username='Example_User', first_name='User', last_name='Example')
        u.set_unusable_password()
        u.save()
        new_job_info.user = u

        new_job_info.save()
        new_bamm = Bamm(
            job_id=new_job_info,
            Motif_Initialization='Custom File',
            Motif_Init_File_Format='PWM',
            num_init_motifs=3,
            model_Order=4,
            extend=4,
            num_motifs=3,
        )
        new_bamm.save()


        upload_example_fasta(new_bamm.job_id)
        upload_example_motif(new_bamm.job_id)

        run_bamm.delay(new_bamm.job_id.job_id)

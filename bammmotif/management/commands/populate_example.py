from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from bammmotif.models import Job
from bammmotif.tasks import run_bamm
import datetime
from ...utils import (
    upload_example_fasta,
    upload_example_motif
)


class Command(BaseCommand):
    def handle(self, *args, **options):

        # create parent job
        new_entry = Job(
            job_ID='293aae88-6e1e-48ba-ad87-19e7304e0393',
            job_name='Example Data ',
            created_at=datetime.datetime.now(),
            mode='Prediction',
            Motif_Initialization='Custom File',
            Motif_Init_File_Format='PWM',
            num_init_motifs=1,
            model_Order=4,
            extend=4,
            num_motifs=3,
            complete=True
            )
        u = User(username='Sample_User', first_name='User', last_name='Example')
        u.set_unusable_password()
        u.save()
        new_entry.user = u

        new_entry.save()

        upload_example_fasta(new_entry.job_ID)
        upload_example_motif(new_entry.job_ID)

        run_bamm.delay(new_entry.job_ID)

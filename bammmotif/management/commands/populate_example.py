from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files import File
from bammmotif.models import *
from bammmotif.forms import *
from bammmotif.tasks import *
from uuid import UUID
from pandas import DataFrame
import datetime
import subprocess
import os
import sys

class Command(BaseCommand):
    def handle(self, *args, **options):
         
        # create parent job 
        new_entry = Job(
            job_ID     = '293aae88-6e1e-48ba-ad87-19e7304e0391',
            job_name   = 'ExampleDataPredicion',
            created_at = datetime.datetime.now(),
            mode       = 'Predicition',
            Motif_Initialization = 'Custom File',
            Motif_Init_File_Format = 'PWM',
            num_init_motifs = 7,
            model_Order  = 4,
            reverse_Complement = True,
            extend_1 = 4,
            extend_2 = 4,
            )

        u = User(username='Example', first_name='Anonymous', last_name='User')
        u.set_unusable_password()
        u.save()

        new_entry.user = u

        filename= '/code/example_data/Hepg2JunD.fasta'
        f = open(str(filename))
        new_entry.Input_Sequences.save(filename, File(f))

        filename= '/code/example_data/Hepg2JunD.peng'
        f = open(str(filename))
        new_entry.Motif_InitFile.save(filename, File(f))

        new_entry.save()
        
        run_example.delay(new_entry.pk)
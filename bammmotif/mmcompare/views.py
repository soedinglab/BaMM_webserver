from datetime import datetime

from django.core import files
from django.db import transaction
from django.shortcuts import (
    render,
)
from django.conf import settings

from ..models import JobInfo
from .models import MMcompareJob

from .forms import MMCompareForm, MMCompareExampleForm
from ..utils import (
    get_user,
)

from .tasks import mmcompare_pipeline


def run_compare_view(request, mode='normal'):
    if request.method == 'POST':
        if mode == 'example':
            form = MMCompareExampleForm(request.POST, request.FILES)
        else:
            form = MMCompareForm(request.POST, request.FILES)
        if form.is_valid():
            meta_job = JobInfo()
            meta_job.created_at = datetime.now()
            meta_job.user = get_user(request)
            meta_job.mode = "Compare"
            meta_job.save()

            # read in data and parameter
            job = form.save(commit=False)
            job.meta_job = meta_job

            job_pk = meta_job.job_id
            if meta_job.job_name is None:
                job_id_short = str(meta_job).split("-", 1)
                meta_job.job_name = job_id_short[0]

            # if example is requested, load the sampleData
            if mode == 'example':
                out_filename = "ExampleMotif.meme"
                with open(settings.EXAMPLE_MOTIF) as handle:
                    job.Motif_InitFile.save(out_filename, files.File(handle))
                job.Motif_Initialization = 'CustomFile'
                job.Motif_Init_File_Format = 'PWM'

            with transaction.atomic():
                meta_job.save()
                job.save()

            mmcompare_pipeline.delay(job_pk)
            return render(request, 'job/submitted.html', {'pk': job_pk})

    if mode == 'example':
        form = MMCompareExampleForm()
    else:
        form = MMCompareForm()
    return render(request, 'compare/compare_input.html',
                  {'form': form, 'mode': mode})

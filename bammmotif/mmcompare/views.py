from datetime import datetime
import os

from django.core import files
from django.db import transaction
from django.shortcuts import (
    render,
    get_object_or_404,
)
from django.conf import settings

from ..models import JobInfo
from .models import MMcompareJob

from .forms import MMCompareForm, MMCompareExampleForm
from ..utils import (
    get_user,
    get_result_folder,
    get_log_file,
)

from .tasks import mmcompare_pipeline
from ..forms import MetaJobNameForm


def run_compare_view(request, mode='normal'):
    if request.method == 'POST':
        meta_job_form = MetaJobNameForm(request.POST)
        if mode == 'example':
            form = MMCompareExampleForm(request.POST, request.FILES)
        else:
            form = MMCompareForm(request.POST, request.FILES)
        if form.is_valid() and meta_job_form.is_valid():
            meta_job = meta_job_form.save(commit=False)
            meta_job.created_at = datetime.now()
            meta_job.user = get_user(request)
            meta_job.mode = "Compare"
            meta_job.job_type = 'compare'
            meta_job.save()

            # read in data and parameter
            job = form.save(commit=False)
            job.meta_job = meta_job

            job_pk = meta_job.job_id

            if meta_job.job_name is None:
                job_id_short = str(meta_job).split("-", maxsplit=1)
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
            return render(request, 'job/submitted.html', {
                'pk': job_pk,
                'result_target': 'compare_results',
            })

    meta_job_form = MetaJobNameForm()
    if mode == 'example':
        form = MMCompareExampleForm()
    else:
        form = MMCompareForm()
    return render(request, 'compare/compare_input.html',
                  {'form': form, 'meta_job_form': meta_job_form, 'mode': mode})


def result_detail(request, pk):
    result = get_object_or_404(MMcompareJob, pk=pk)
    meta_job = result.meta_job
    opath = get_result_folder(pk)
    filename_prefix = result.filename_prefix

    motif_db = result.motif_db
    db_dir = motif_db.relative_db_model_dir

    if meta_job.complete:
        num_logos = range(1, (min(3, result.model_order+1)))
        return render(request, 'compare/result_detail.html',
                      {'result': result, 'opath': opath,
                       'mode': meta_job.mode,
                       'Output_filename': filename_prefix,
                       'num_logos': num_logos,
                       'db_dir': db_dir})
    else:
        log_file = get_log_file(pk)
        command = "tail -20 %r" % log_file
        output = os.popen(command).read()
        return render(request, 'results/result_status.html', {
            'job_id': pk,
            'job_name': meta_job.job_name,
            'status': meta_job.status,
            'output': output
        })

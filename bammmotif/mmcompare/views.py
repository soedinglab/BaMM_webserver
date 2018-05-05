import os
import itertools

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
    register_job_session,
    check_motif_input,
)

from ..views import redirect_if_not_ready

from .tasks import mmcompare_pipeline
from ..forms import MetaJobNameForm


def run_compare_view(request, mode='normal'):
    if request.method == 'POST':
        meta_job_form = MetaJobNameForm(request.POST)
        if mode == 'example':
            form = MMCompareExampleForm(request.POST, request.FILES)
        else:
            form = MMCompareForm(request.POST, request.FILES)
        is_valid = form.is_valid() and meta_job_form.is_valid()
        if is_valid:
            meta_job = meta_job_form.save(commit=False)
            meta_job.user = get_user(request)
            meta_job.mode = "Compare"
            meta_job.job_type = 'mmcompare'
            meta_job.save()

            # read in data and parameter
            job = form.save(commit=False)
            job.meta_job = meta_job
            job_pk = meta_job.job_id

            is_valid = check_motif_input(job, form, request)

            if is_valid:
                if meta_job.job_name is None:
                    job_id_short = str(meta_job).split("-", maxsplit=1)
                    meta_job.job_name = job_id_short[0]

                # if example is requested, load the sampleData
                if mode == 'example':
                    out_filename = "ExampleMotif.meme"
                    with open(settings.EXAMPLE_MOTIF) as handle:
                        job.Motif_InitFile.save(out_filename, files.File(handle))
                    job.Motif_Initialization = 'CustomFile'
                    job.Motif_Init_File_Format = 'MEME'

                with transaction.atomic():
                    meta_job.save()
                    register_job_session(request, meta_job)
                    job.save()

                mmcompare_pipeline.delay(job_pk)
                return render(request, 'job/submitted.html', {
                    'pk': job_pk,
                    'result_target': 'compare_results',
                })
    else:
        is_valid = True
        meta_job_form = MetaJobNameForm()
        if mode == 'example':
            form = MMCompareExampleForm()
        else:
            form = MMCompareForm()

    return render(request, 'compare/compare_input.html', {
        'job_form': form,
        'metajob_form': meta_job_form,
        'mode': mode,
        'all_form_fields': itertools.chain(form, meta_job_form),
        'max_file_size': settings.MAX_UPLOAD_FILE_SIZE,
        'validation_errors': not is_valid,
    })


def result_detail(request, pk):

    redirect_obj = redirect_if_not_ready(pk)
    if redirect_obj is not None:
        return redirect_obj

    result = get_object_or_404(MMcompareJob, pk=pk)
    meta_job = result.meta_job
    opath = get_result_folder(pk)
    filename_prefix = result.filename_prefix

    motif_db = result.motif_db
    db_dir = motif_db.relative_db_model_dir

    num_logos = range(1, (min(3, result.model_order+1)))
    return render(request, 'compare/result_detail.html',
                  {'result': result, 'opath': opath,
                   'mode': meta_job.mode,
                   'Output_filename': filename_prefix,
                   'num_logos': num_logos,
                   'db_dir': db_dir})

from os import path
import itertools

from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import transaction

from ..forms import MetaJobNameForm
from . import forms as bamm_forms

from ..utils import (
    get_result_folder,
    set_job_name_if_unset,
    check_fasta_input,
    register_job_session,
    get_user,
    upload_example_fasta,
)
from ..views import redirect_if_not_ready
from .models import OneStepBaMMJob

from .tasks import denovo_pipeline


ONESTEP_JOBFORM = {
    'example': bamm_forms.OneStepBammJobExampleForm,
    'denovo': bamm_forms.OneStepBammJobForm
}


def one_step_denovo(request, mode='denovo'):
    max_file_size = settings.MAX_UPLOAD_FILE_SIZE
    if request.method == 'POST':
        metajob_form = MetaJobNameForm(request.POST)
        job_form = ONESTEP_JOBFORM[mode](request.POST, request.FILES)

        is_valid = metajob_form.is_valid() and job_form.is_valid()
        if is_valid:
            meta_job = metajob_form.save(commit=False)
            meta_job.user = get_user(request)
            meta_job.mode = "De-novo"
            meta_job.job_type = 'denovo'
            set_job_name_if_unset(meta_job)

            job = job_form.save(commit=False)
            job.meta_job = meta_job
            job_pk = meta_job.pk

            if mode == 'example':
                upload_example_fasta(job)
            else:
                is_valid = check_fasta_input(job, job_form, request.FILES)

            if is_valid:
                with transaction.atomic():
                    job.meta_job.save()
                    register_job_session(request, job.meta_job)
                    job.save()

                denovo_pipeline.delay(job_pk)

                return render(request, 'job/submitted.html', {
                    'pk': job_pk,
                    'result_target': 'denovo',
                })

    else:
        metajob_form = MetaJobNameForm()
        job_form = ONESTEP_JOBFORM[mode](initial={'max_refined_motifs': settings.DEFAULT_SEEDS_FOR_REFINEMENT})
        is_valid = True

    return render(request, 'denovo/one_step_denovo.html', {
        'metajob_form': metajob_form,
        'job_form': job_form,
        'max_file_size': max_file_size,
        'all_form_fields': itertools.chain(metajob_form, job_form),
        'mode': mode,
        'validation_errors': not is_valid,
        'max_seeds': settings.MAX_SEEDS_FOR_REFINEMENT,
    })


def denovo_results(request, pk):
    redirect_obj = redirect_if_not_ready(pk)
    if redirect_obj is not None:
        return redirect_obj

    result = get_object_or_404(OneStepBaMMJob, meta_job__pk=pk)
    motif_db = result.motif_db
    db_dir = motif_db.relative_db_model_dir

    num_logos = range(1, (min(2, result.model_order)+1))
    return render(request, 'bamm/bamm_result_detail.html', {
        'result': result, 'opath': get_result_folder(pk),
        'mode': result.meta_job.mode,
        'Output_filename': result.filename_prefix,
        'num_logos': num_logos,
        'db_dir': db_dir,
    })

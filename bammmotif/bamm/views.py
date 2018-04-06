from os import path
import itertools

from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.db import transaction

from ..forms import MetaJobNameForm
from . import forms as bamm_forms

from ..utils import (
    set_job_name_if_unset,
    check_fasta_input,
    register_job_session,
    get_user,
    upload_example_fasta,
)

from .tasks import denovo_pipeline


ONESTEP_JOBFORM = {
    'example': bamm_forms.OneStepBammJobExampleForm,
    'normal': bamm_forms.OneStepBammJobForm
}


def one_step_denovo(request, mode='normal'):
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

                # TODO run pipeline
                denovo_pipeline.delay(job_pk)

                return render(request, 'job/submitted.html', {
                    'pk': job_pk,
                    'result_target': 'denovo',
                })

    else:
        metajob_form = MetaJobNameForm()
        job_form = ONESTEP_JOBFORM[mode]()
        is_valid = True

    return render(request, 'denovo/one_step_denovo.html', {
        'metajob_form': metajob_form,
        'job_form': job_form,
        'max_file_size': max_file_size,
        'all_form_fields': itertools.chain(metajob_form, job_form),
        'mode': mode,
        'validation_errors': not is_valid,
    })


def denovo_results(request, pk):
    pass

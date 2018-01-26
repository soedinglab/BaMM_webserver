from django.utils import timezone
from django.shortcuts import get_object_or_404, render

from .forms import (
    BaMMScanExampleForm,
    BaMMScanDBForm,
    BaMMScanForm
)
from ..forms import MetaJobNameForm

from ..utils import (
    get_user,
    set_job_name,
    upload_example_fasta,
    upload_example_motif,
)

from .tasks import bamm_scan_pipeline


def run_bammscan_view(request, mode='normal', pk='null'):
    if request.method == "POST":
        meta_job_form = MetaJobNameForm(request.POST)
        if mode == 'example':
            form = BaMMScanExampleForm(request.POST, request.FILES)
        elif mode == 'db':
            form = BaMMScanDBForm(request.POST, request.FILES)
        elif mode == 'normal':
            form = BaMMScanForm(request.POST, request.FILES)

        if form.is_valid() and meta_job_form.is_valid():
            meta_job = meta_job_form.save(commit=False)
            meta_job.created_at = timezone.now()
            meta_job.user = get_user(request)
            meta_job.mode = "BaMMScan"
            meta_job.save()

            if meta_job.job_name is None:
                job_id_short = str(meta_job).split("-", maxsplit=1)
                meta_job.job_name = job_id_short[0]

            job = form.save(commit=False)
            job.meta_job = meta_job
            job_pk = meta_job.pk

            # if example is requested, load the sampleData
            if mode == 'example':
                upload_example_fasta(job)
                upload_example_motif(job)

            # enter db input
            if mode == 'db':
                pass
                # this is currently not implemented

            job.save()

            bamm_scan_pipeline.delay(job_pk)
            return render(request, 'job/submitted.html', {'pk': job_pk})

    meta_job_form = MetaJobNameForm()
    if mode == 'example':
        form = BaMMScanExampleForm()
    if mode == 'normal':
        form = BaMMScanForm()
    return render(request, 'job/bammscan_input.html',
                  {
                      'form': form,
                      'meta_job_form': meta_job_form,
                      'mode': mode,
                  })

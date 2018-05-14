import os
import glob
from urllib.parse import urljoin

from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404

from django.conf import settings
from django.utils import timezone
from django.http import FileResponse, Http404

from .models import (
    JobSession,
    JobInfo,
)
from .utils import (
    get_log_file,
    get_session_key,
    url_prefix,
    get_job_output_folder,
)
from .forms import FindForm, GenomeBrowserForm

import logging

logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'home/home.html')


def info(request):
    return render(request, 'home/aboutBaMMmotif.html')


def documentation(request):
    return render(request, 'home/documentation.html')


def links(request):
    return render(request, 'home/links.html')


def contact(request):
    return render(request, 'home/contact.html')


def imprint(request):
    return render(request, 'home/imprint.html')


def submitted(request, pk):
    return render(request, 'job/submitted.html', {'pk': pk})


def find_results_by_id(request, pk):
    job_id = pk
    meta_job = get_object_or_404(JobInfo, job_id=job_id)

    if not meta_job.complete:
        log_file = get_log_file(pk)
        command = "tail -20 %r" % log_file
        output = os.popen(command).read()
        return render(request, 'results/result_status.html', {
            'output': output,
            'job_id': meta_job.pk,
            'job_name': meta_job.job_name,
            'status': meta_job.status,
        })

    else:
        base = request.build_absolute_uri('/')
        url = urljoin(base, url_prefix[meta_job.job_type] + '/' + job_id)
        return redirect(url, permanent=True)


def find_results(request):
    session_key = get_session_key(request)
    min_time = timezone.now() - timezone.timedelta(days=settings.MAX_FINDJOB_DAYS)
    session_jobs = JobSession.objects.filter(session_key=session_key, job__created_at__gt=min_time)

    if request.method == "POST":
        form = FindForm(request.POST)
        if form.is_valid():
            jobid = form.cleaned_data['job_ID']
            meta_job = get_object_or_404(JobInfo, job_id=jobid)
            base = request.build_absolute_uri('/')
            url = urljoin(base, url_prefix[meta_job.job_type] + '/' + jobid)
            return redirect(url, permanent=True)
    return render(request, 'results/results_main.html', {
        'form': FindForm(),
        'jobs': session_jobs,
    })


def redirect_if_not_ready(job_id):
    meta_job = get_object_or_404(JobInfo, job_id=job_id)
    if not meta_job.complete:
        return redirect('find_results_by_id', pk=job_id)


def serve_bed_file(request, job_id, motif_no):
    job = get_object_or_404(JobInfo, job_id=job_id)
    job_folder = get_job_output_folder(job.job_id)
    bed_files = glob.glob(os.path.join(job_folder, '*_motif_%s.bed' % motif_no))
    print(os.path.join(job_folder, '_motif_%s.bed' % motif_no))
    if len(bed_files) != 1:
        raise Http404()
    response = FileResponse(open(bed_files[0], 'rb'))
    response['Content-Type'] = 'text/plain'
    return response


def run_genome_browser(request):
    form = GenomeBrowserForm(request.POST)

    if not form.is_valid():
        logger.error('programming error: form should always be valid here.')

    job_id = form.cleaned_data['job_id']
    motif_id = form.cleaned_data['motif_id']
    organism = form.cleaned_data['organism']
    assembly_id = form.cleaned_data['assembly_id']

    absolute_root = request.build_absolute_uri('/')[:-1]
    bed_file_url = '%s/bedtrack/%s/%s' % (absolute_root, job_id, motif_id)
    ucsc_url = (
        'https://genome.ucsc.edu/cgi-bin/hgTracks?'
        + 'org=%s&' % organism
        + 'db=%s&' % assembly_id
        + 'hgt.customText=%s' % bed_file_url
    )
    return redirect(ucsc_url)

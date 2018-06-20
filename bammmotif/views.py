import os
from os import path
import subprocess
import io
import glob
from urllib.parse import urljoin
import logging

from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)
from django.http import (
    HttpResponse,
    FileResponse,
    JsonResponse,
    Http404,
)
from django.conf import settings
from django.utils import timezone

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
from .utils.occur2bed import get_viewpoint


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


def get_job_status(request, pk):
    job_id = pk
    meta_job = get_object_or_404(JobInfo, job_id=job_id)
    return JsonResponse({'status': meta_job.status})


def find_results_by_id(request, pk):
    job_id = pk
    meta_job = get_object_or_404(JobInfo, job_id=job_id)

    if not meta_job.complete:
        log_file = get_log_file(pk)
        command = 'tail -20 %r' % log_file

        if not path.exists(log_file):
            output = '(job still queueing)'
        else:
            output = subprocess.getoutput(command)

        return render(request, 'results/result_status.html', {
            'output': output,
            'job_id': meta_job.pk,
            'job_name': meta_job.job_name,
            'status': meta_job.status,
        })

    else:
        base = request.build_absolute_uri('/')
        url = urljoin(base, url_prefix[meta_job.job_type] + '/' + job_id)
        return redirect(url)


def get_session_jobs(request):
    session_key = get_session_key(request)
    min_time = timezone.now() - timezone.timedelta(days=settings.MAX_FINDJOB_DAYS)
    session_jobs = JobSession.objects.filter(session_key=session_key, job__created_at__gt=min_time)
    return session_jobs


def find_results(request):
    session_jobs = get_session_jobs(request)

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
    if len(bed_files) != 1:
        raise Http404()
    response = FileResponse(open(bed_files[0], 'rb'))
    response['Content-Type'] = 'text/plain'
    return response


def run_genome_browser(request):
    form = GenomeBrowserForm(request.POST)

    if not form.is_valid():
        logger.error('programming error: form should always be valid here.')
        return HttpResponse(status=500)

    job_id = form.cleaned_data['job_id']
    motif_id = form.cleaned_data['motif_id']
    organism = form.cleaned_data['organism']
    assembly_id = form.cleaned_data['assembly_id']

    absolute_root = request.build_absolute_uri('/')[:-1]

    bed_file_url = '%s/bedtrack/%s/%s/' % (absolute_root, job_id, motif_id)

    job_folder = get_job_output_folder(job_id)
    bed_files = glob.glob(os.path.join(job_folder, '*_motif_%s.bed' % motif_id))
    if len(bed_files) != 1:
        logger.error('programming error: there should only be exactly one bedfile matching.')
        return HttpResponse(status=500)
    bed_file = bed_files[0]

    chrom, start, end = get_viewpoint(bed_file)
    new_start = max(1, start - 30)
    new_end = end + 30
    position_str = '%s:%s-%s' % (chrom, new_start, new_end)

    ucsc_url = (
        'https://genome.ucsc.edu/cgi-bin/hgTracks?'
        + 'org=%s&' % organism
        + 'db=%s&' % assembly_id
        + 'position=%s&' % position_str
        + 'hgt.customText=%s' % bed_file_url
    )
    return redirect(ucsc_url)


def serve_job_csv(request):
    session_jobs = get_session_jobs(request)
    sorted_jobs = session_jobs.order_by('-job__created_at')
    csv_obj = io.StringIO()
    header = [
        'submission_time', 'job_name',
        'job_id', 'job_type', 'job_status'
    ]
    print(*header, sep=',', file=csv_obj)
    for job_session in sorted_jobs:
        job = job_session.job
        tokens = [
            job.created_at,
            job.job_name,
            job.job_id,
            job.job_type,
            job.status,
        ]
        print(*tokens, sep=',', file=csv_obj)
    csv_obj.seek(0)

    csv_string = csv_obj.read()
    bytes_response = csv_string.encode('utf-8')

    response = HttpResponse(bytes_response, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=bammserver_joblist.csv'
    return response

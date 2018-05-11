import os
from urllib.parse import urljoin

from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404

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
)
from .forms import FindForm


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

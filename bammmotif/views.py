from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from bammmotif.models import JobInfo
from bammmotif.utils.misc import url_prefix
from .forms import FindForm
from urllib.parse import urljoin


# #########################
# ## HOME and GENERAL VIEWS #########################


def home(request):
    return render(request, 'home/home.html')


def info(request):
    return render(request, 'home/aboutBaMMmotif.html')


def documentation(request):
    return render(request, 'home/documentation.html')


def download(request):
    return render(request, 'home/download.html')


def contact(request):
    return render(request, 'home/contact.html')


def imprint(request):
    return render(request, 'home/imprint.html')


# #########################
# ## JOB RELATED VIEWS
# #########################

def submitted(request, pk):
    return render(request, 'job/submitted.html', {'pk': pk})


# #########################
# ## RESULT RELATED VIEWS
# #########################


def find_results_by_id(request, pk):
    job_id = pk
    meta_job = get_object_or_404(JobInfo, job_id=job_id)
    base = request.build_absolute_uri('/')
    url = urljoin(base, url_prefix[meta_job.job_type] + job_id)
    return redirect(url, permanent=True)


def find_results(request):
    session_key = get_session_key(request)
    session_jobs = JobSession.objects.filter(session_key=session_key)

    if request.method == "POST":
        form = FindForm(request.POST)
        if form.is_valid():
            jobid = form.cleaned_data['job_ID']
            meta_job = get_object_or_404(JobInfo, job_id=jobid)
            base = request.build_absolute_uri('/')
            url = urljoin(base, url_prefix[meta_job.job_type] + jobid)
            return redirect(url, permanent=True)
    return render(request, 'results/results_main.html', {
        'form': FindForm(),
        'jobs': session_jobs,
    })


def delete(request, pk):
    Job.objects.filter(job_ID=pk).delete()
    if request.user.is_authenticated():
        user_jobs = Job.objects.filter(user=request.user.id)
        return render(request, 'results/result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_results')

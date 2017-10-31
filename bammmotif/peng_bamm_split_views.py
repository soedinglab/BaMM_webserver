from django.shortcuts import render

from .forms import JobForm
from .peng_bamm_split_form import get_valid_form
from .peng_bamm_split_job import create_job, validate_input_data
from .tasks import run_bamm
from .models import Job

def data_predict_peng(request):
    print("ENTERING Data PREDICT VIEW data_peng_changed")
    if request.method == "POST":
        print("Request IS POST")
        # Reformat get valid form.
        form, valid, args = get_valid_form(request.POST, request.FILES, request.user)
        if not valid:
            return render(request, 'job/de_novo_search.html', args)
        job = create_job(form, request.user)
        ret, valid_input = validate_input_data(job)
        if not valid_input:
            Job.objects.filter(job_ID=job.pk).delete()
            return render(request, 'job/de_novo_search.html', {'form': JobForm(), 'type': "Fasta", 'message': ret})
        #TODO: Change to run_peng.delay(job.ok)
        run_bamm.delay(job.pk)
        return render(request, 'job/submitted.html', {'pk': job.pk})
    print("Request IS NOT POST -> make form and redirect")
    return render(request, 'job/de_novo_search.html', {'form': JobForm(), 'type': "OK", 'message': "OK"})

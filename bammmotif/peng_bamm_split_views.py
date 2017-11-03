from os import path
import os
from django.shortcuts import render, get_object_or_404, redirect

from .peng_bamm_split_form import get_valid_peng_form, PengExampleForm, PengForm
from .peng_bamm_split_job import create_job, validate_input_data
from .peng_bamm_split_tasks import run_peng
from .peng_bamm_split_utils import upload_example_fasta_for_peng
from .models import Job, PengJob, DbParameter
from .utils import get_result_folder, get_log_file


def peng_result_detail(request, pk):
    result = get_object_or_404(PengJob, pk=pk)
    opath = get_result_folder(pk)
    Output_filename = result.Output_filename()

    database = 100
    db = get_object_or_404(DbParameter, pk=database)
    db_dir = path.join(db.base_dir, 'Results')

    if result.complete:
        print("status is successfull")
        num_logos = range(1, (min(2, result.model_Order)+1))
        if result.mode == "Prediction" or result.mode == "Compare":
            return render(request, 'results/result_detail.html',
                          {'result': result, 'opath': opath,
                           'mode': result.mode,
                           'Output_filename': Output_filename,
                           'num_logos': num_logos,
                           'db_dir': db_dir})
        elif result.mode == "Occurrence":
            return redirect('result_occurrence', result.mode, pk)

    else:
        print('status not ready yet')
        log_file = get_log_file(pk)
        command = "tail -20 %r" % log_file
        output = os.popen(command).read()
        return render(request, 'results/result_status.html',
                      {'result': result, 'opath': opath, 'output': output})


def run_peng_view(request, mode='normal'):
    print("ENTERING Data PREDICT VIEW data_peng_changed: ", request.method, mode)
    if request.method == "POST":
        print("run_peng_view: Request IS POST")
        # Reformat get valid form.
        form, valid, args = get_valid_peng_form(request.POST, request.FILES, request.user, mode)
        if not valid:
            print("FORM IS NOT VALID!!!!!")
            pass
            # return render(request, 'job/de_novo_search.html', args)
        peng_job = create_job(form, request)
        print("PENG_JOB finished successfully!")
        ret, valid_input = validate_input_data(peng_job)
        print("VALID_INPUT: ", valid_input)
        if not valid_input:
            Job.objects.filter(job_ID=peng_job.pk).delete()
            # return render(request, 'job/de_novo_search.html', {'form': PengForm(), 'type': "Fasta", 'message': ret})
        if mode == 'example':
            upload_example_fasta_for_peng(peng_job.job_ID)
        print("Running Peng")
        run_peng.delay(peng_job.job_ID)
        # run_bamm.delay(peng_job.pk)
        return render(request, 'job/submitted.html', {'pk': peng_job.job_ID})
    if mode == 'example':
        form = PengExampleForm()
    else:
        form = PengForm()
    print("Request IS NOT POST -> make form and redirect")
    return render(request, 'job/peng_bamm_split_peng_input.html',
                  {'form': form, 'mode': mode})

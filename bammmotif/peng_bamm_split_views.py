import os
from django.shortcuts import render, get_object_or_404, redirect


from .peng_bamm_split_form import get_valid_peng_form, PengExampleForm, PengForm
from .peng_bamm_split_job import create_job, validate_input_data
from .peng_bamm_split_tasks import run_peng
from .peng_bamm_split_utils import upload_example_fasta_for_peng
from .models import Job, PengJob, DbParameter
<<<<<<< HEAD
from .forms import FindForm
from .peng_bamm_split_job import file_path_peng
from .peng_utils import get_motif_ids, plot_meme_output
from .utils import get_result_folder

def peng_result_detail(request, pk):
    result = get_object_or_404(PengJob, pk=pk)
    meme_result_file_path = file_path_peng(result.job_ID, result.meme_output)
    # opath = get_result_folder(pk)

    # database = 100
    # db = get_object_or_404(DbParameter, pk=database)
    # db_dir = path.join(db.base_dir, 'Results')

    if result.complete:
        print("status is successfull")
        print("now plot result")
        plot_output_directory = os.path.join(meme_result_file_path.rsplit('/', maxsplit=1)[0], "meme_plots")
        opath = os.path.join(get_result_folder(result.job_ID), "meme_plots")
        if not os.path.exists(plot_output_directory):
            os.makedirs(plot_output_directory)
        motif_ids = get_motif_ids(meme_result_file_path)
        plot_paths = {}
        for motif in motif_ids:
            target_file = os.path.join(plot_output_directory, motif + ".png")
            plot_meme_output(target_file, motif, meme_result_file_path)
            plot_paths[motif] = target_file
        print(plot_paths)
        return render(request, 'results/peng_result_detail.html',
                        {'result': result,
                         'mode': result.mode,
                         'motif_ids': motif_ids,
                         'result_directory': plot_output_directory,
                         'opath': opath,
                         })
    else:
        print('status not ready yet')
        #log_file = get_log_file(pk)
        #command = "tail -20 %r" % log_file
        #output = os.popen(command).read()
        output = "12345"
        opath  = "aklsdklsam"
        return render(request, 'results/peng_result_status.html',
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
        return render(request, 'job/peng_bamm_split_submitted.html', {'pk': peng_job.job_ID})
    if mode == 'example':
        form = PengExampleForm()
    else:
        form = PengForm()
    print("Request IS NOT POST -> make form and redirect")
    return render(request, 'job/peng_bamm_split_peng_input.html',
                  {'form': form, 'mode': mode})

def find_peng_results(request, pk):
    if request.method == "POST":
        form = FindForm(request.POST)
        if form.is_valid():
            jobid = form.cleaned_data['job_ID']
            return redirect('peng_result_detail', pk=jobid)
        form = FindForm()
    return render(request, 'results/peng_results_main.html', {'form': form})

def peng_result_overview(request, pk):
    if request.user.is_authenticated():
        user_jobs = PengJob.objects.filter(user=request.user.id)
        return render(request, 'results/peng_result_overview.html',
                      {'user_jobs': user_jobs})
    else:
        return redirect(request, 'find_peng_results')


import os

from django.conf import settings
from django.shortcuts import get_object_or_404

from bammmotif.peng.settings import JOB_OUTPUT_DIRECTORY, JOB_INPUT_DIRECTORY, MEME_PLOT_DIRECTORY, MEME_PLOT_INPUT, \
    PENG_OUTPUT_MEME, PENG_TEMP_DIRECTORY, BMSCORE_SUFFIX, PWM2BAMM_DIRECTORY, FILTERPWM_OUTPUT_FILE, PENG_OUTPUT, \
    MEME_OUTPUT_FILE


def job_directory(job_pk):
    return os.path.join(settings.JOB_DIR, job_pk)


def job_output_directory(job_pk):
    return os.path.join(job_directory(job_pk), JOB_OUTPUT_DIRECTORY)


def job_input_directory(job_pk):
    return os.path.join(job_directory(job_pk), JOB_INPUT_DIRECTORY)


def meme_plot_directory(job_pk):
    return os.path.join(job_output_directory(job_pk), MEME_PLOT_DIRECTORY)


def meme_plot_input_file(job_pk):
    return os.path.join(meme_plot_directory(job_pk), MEME_PLOT_INPUT)


def peng_output_meme_file(job_pk):
    return os.path.join(job_output_directory(job_pk), PENG_OUTPUT_MEME)


def peng_temp_directory(job_pk):
    return os.path.join(job_directory(job_pk), PENG_TEMP_DIRECTORY)


def peng_bmscore_file(job_pk, filename_prefix):
    return os.path.join(peng_temp_directory(job_pk), filename_prefix + BMSCORE_SUFFIX)


def bamm_directory(job_pk):
    return os.path.join(job_directory(job_pk), PWM2BAMM_DIRECTORY)


def filter_output_file(job_pk):
    return os.path.join(job_output_directory(job_pk), FILTERPWM_OUTPUT_FILE)


def peng_bmscore_file_old(job_pk, filename_prefix):
    return os.path.join(get_temporary_job_dir(job_pk), filename_prefix + BMSCORE_SUFFIX)


def peng_output_meme_file_old(job_pk):
    return os.path.join(get_job_ouput_directory(job_pk), PENG_OUTPUT_MEME)


def bamm_directory_old(job_pk):
    return os.path.join(get_job_directory(job_pk), PWM2BAMM_DIRECTORY)


def filter_output_file_old(job_pk):
    return os.path.join(get_job_ouput_directory(job_pk), FILTERPWM_OUTPUT_FILE)


def get_meme_result_file_path(job_id):
    return os.path.join(get_job_directory(job_id), JOB_OUTPUT_DIRECTORY, MEME_PLOT_INPUT)


def get_plot_output_directory(job_id):
    meme_path = get_meme_result_file_path(job_id)
    return os.path.join(meme_path.rsplit('/', maxsplit=1)[0], MEME_PLOT_DIRECTORY)


def get_job_ouput_directory(job_id):
    ptj = get_job_directory(job_id)
    p = os.path.join(ptj, JOB_OUTPUT_DIRECTORY)
    if not os.path.exists(p):
        os.makedirs(p)
    return p


def get_job_directory(job_id):
    path_to_job = os.path.join(settings.MEDIA_ROOT, str(job_id))
    if not os.path.exists(path_to_job):
        os.makedirs(path_to_job)
    return path_to_job


def file_path_peng(job_id, filename):
    path_to_job = get_job_directory(job_id)
    #path_to_job = os.path.join(settings.MEDIA_ROOT, str(job_id), PENG_JOB_RESULT)
    #if not os.path.exists(path_to_job):
    #    os.makedirs(path_to_job)
    return os.path.join(path_to_job, str(filename))


def file_path_peng_meta(job_id, filename):
    path_to_job = os.path.join(settings.MEDIA_ROOT, str(job_id), JOB_OUTPUT_DIRECTORY)
    if not os.path.exists(path_to_job):
        os.makedirs(path_to_job)
    return os.path.join(path_to_job, str(filename))


def peng_meme_directory(job_id):
    path_to_plots = os.path.join(settings.MEDIA_ROOT, str(job_id), JOB_OUTPUT_DIRECTORY)
    if not os.path.exists(path_to_plots):
        os.makedirs(path_to_plots)
    return path_to_plots


def job_directory_path_peng(instance, filename, intermediate_dir="Input"):
    path = os.path.join(settings.MEDIA_ROOT, str(instance.job_id), intermediate_dir)
    if not os.path.exists(path):
        os.makedirs(path)
    return os.path.join(path, str(filename))


def get_temporary_job_dir(job_pk):
    return os.path.join(get_job_directory(job_pk), PENG_TEMP_DIRECTORY)


def get_bmscore_filename(job_pk, job_type):
    job = get_object_or_404(job_type, pk=job_pk)
    fname = job.fasta_file.name.split('/')[-1]
    return fname.rsplit('.', maxsplit=1)[0] + ".bmscore"


def get_peng_output_in_bamm_directory(job_pk):
    return os.path.join(get_job_directory(job_pk), PENG_OUTPUT)


def get_peng_meme_output_in_bamm(job_pk):
    return os.path.join(get_peng_output_in_bamm_directory(job_pk), MEME_OUTPUT_FILE)


def get_memeplot_directory_in_bamm(job_pk):
    return os.path.join(get_peng_output_in_bamm_directory(job_pk), MEME_PLOT_DIRECTORY)


def get_bmscore_path(job):
    return os.path.join(get_temporary_job_dir(job.job_id.job_id), job.filename_prefix)


def media_memeplot_directory_html(job_pk):
    return os.path.join(str(job_pk), JOB_OUTPUT_DIRECTORY, MEME_PLOT_DIRECTORY)


def media_bammplot_directory_html(job_pk):
    return os.path.join('jobs', str(job_pk), JOB_OUTPUT_DIRECTORY, MEME_PLOT_DIRECTORY)


def media_memeplot_directory_from_peng_html(job_pk):
    return os.path.join(str(job_pk), PENG_OUTPUT, MEME_PLOT_DIRECTORY)
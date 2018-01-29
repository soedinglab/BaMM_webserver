import os
from os import path

from django.conf import settings

from ..utils import (
    get_job_output_folder,
)


JOB_OUTPUT_DIRECTORY = 'Output'
PENG_OUTPUT = 'pengoutput'
PENG_INPUT = 'Input'
SELECTED_MOTIFS = 'selected_motifs'
MEME_PLOT_DIRECTORY = 'meme_plots'
MEME_OUTPUT_FILE = 'out.meme'
MOTIF_SELECT_IDENTIFIER = "_select"
JSON_OUTPUT_FILE = "out.json"


#Filter PWM
PATH_TO_FILTERPWM_SCRIPT = '/ext/filterPWMs/filterPWM.py'
FILTERPWM_INPUT_FILE = MEME_OUTPUT_FILE
#Overwrite for now
FILTERPWM_OUTPUT_FILE = 'out_filtered.meme'

#Meme plotting
MEME_PLOT_INPUT = FILTERPWM_OUTPUT_FILE

FASTA_VALIDATION_SCRIPT = '/code/bammmotif/static/scripts/valid_fasta'
ZIPPED_MOTIFS = 'motif_all.zip'
EXAMPLE_FASTA_FILE = 'ExampleData.fasta'

#ERROR MESSAGES
NOT_ENOUGH_MOTIFS_SELECTED_FOR_REFINEMENT = "Please select at least one motif to start refinement!"

# models related variables
ALLOWED_JOBMODES = [
    "peng",
]


def get_meme_result_file_path(job_id):
    return path.join(get_job_output_folder(job_id), MEME_PLOT_INPUT)


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

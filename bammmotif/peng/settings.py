import os
from django.conf import settings


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

# models related variables
ALLOWED_JOBMODES = [
    "peng",
]

def get_job_ouput_directory(job_id):
    ptj = get_job_directory(job_id)



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


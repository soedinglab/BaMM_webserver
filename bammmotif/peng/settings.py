import os
from django.conf import settings



PENG_JOB_RESULT = 'Output'
PENG_OUTPUT = 'pengoutput'
PENG_INPUT = 'Input'
SELECTED_MOTIFS = 'selected_motifs'
MEME_PLOT_DIRECTORY = 'meme_plots'
MEME_OUTPUT_FILE = 'out.meme'
MOTIF_SELECT_IDENTIFIER = "_select"
JSON_OUTPUT_FILE = "out.json"


FASTA_VALIDATION_SCRIPT = '/code/bammmotif/static/scripts/valid_fasta'
ZIPPED_MOTIFS = 'motif_all.zip'
EXAMPLE_FASTA_FILE = 'ExampleData.fasta'

# models related variables
ALLOWED_JOBMODES = [
    "peng",
]


def file_path_peng(job_id, filename):
    path_to_job = os.path.join(settings.MEDIA_ROOT, str(job_id), PENG_JOB_RESULT)
    if not os.path.exists(path_to_job):
        os.makedirs(path_to_job)
    return os.path.join(path_to_job, str(filename))

def file_path_peng_meta(job_id, filename):
    path_to_job = os.path.join(settings.MEDIA_ROOT, str(job_id), PENG_JOB_RESULT)
    if not os.path.exists(path_to_job):
        os.makedirs(path_to_job)
    return os.path.join(path_to_job, str(filename))

def peng_meme_directory(job_id):
    path_to_plots = os.path.join(settings.MEDIA_ROOT, str(job_id), PENG_JOB_RESULT)
    if not os.path.exists(path_to_plots):
        os.makedirs(path_to_plots)
    return path_to_plots

def job_directory_path_peng(instance, filename, intermediate_dir="Input"):
    path = os.path.join(settings.MEDIA_ROOT, str(instance.job_id), intermediate_dir)
    if not os.path.exists(path):
        os.makedirs(path)
    return os.path.join(path, str(filename))


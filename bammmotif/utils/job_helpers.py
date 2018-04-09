from os import path

from django.conf import settings
from django.core import files


from .path_helpers import (
    get_job_input_folder,
    get_job_output_folder,
)

from ..models import (
    Motifs,
)


def get_model_order(job):
    job_pk = job.meta_job.pk
    filename = path.join(get_job_input_folder(job_pk), path.basename(job.Motif_InitFile.name))
    order = -1
    with open(filename) as handle:
        for line in handle:
            tokens = line.split()
            if len(tokens) == 0:
                return order
            else:
                order = order + 1
    return order


def get_bg_model_order(job):
    job_pk = job.meta_job.pk
    filename = path.join(get_job_input_folder(job_pk), path.basename(job.bgModel_File.name))
    order = -1
    with open(filename) as handle:
        _, _, _, order = next(handle).split()
    return int(order)


def add_motif_iupac(job):
    job_pk = job.meta_job.pk
    prefix = job.filename_prefix
    iupac_file = path.join(get_job_output_folder(job_pk), prefix + '.iupac')
    with open(iupac_file) as handle:
        for line in handle:
            tokens = line.split()
            motif = Motifs()
            motif.parent_job = job.meta_job
            motif.job_rank = tokens[1]
            motif.iupac = tokens[2]
            motif.length = tokens[3]
            motif.save()


def upload_example_fasta(job):
    out_filename = "ExampleData.fasta"
    with open(settings.EXAMPLE_FASTA) as handle:
        job.Input_Sequences.save(out_filename, files.File(handle), save=False)


def upload_example_motif(job):
    out_filename = "ExampleMotif.meme"
    with open(settings.EXAMPLE_MOTIF) as handle:
        job.Motif_InitFile.save(out_filename, files.File(handle))
    job.Motif_Initialization = 'CustomFile'
    job.Motif_Init_File_Format = 'PWM'
    job.save()

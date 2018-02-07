from os import path

from django.core import files

from ..utils import filename_relative_to_job_dir


def upload_db_motif(job, motif):
    db_model_path = motif.motif_db.db_model_directory
    model_name = motif.filename_prefix

    # upload model
    model_file = path.join(db_model_path, model_name, model_name + '_motif_1.ihbcp')
    with open(model_file) as handle:
        job.Motif_InitFile.save(model_name + '.ihbcp', files.File(handle))
    job.Motif_Initialization = 'CustomFile'
    job.Motif_Init_File_Format = "BaMM"

    # upload background model
    bg_file = path.join(db_model_path, model_name, model_name + '.hbcp')
    with open(bg_file) as handle:
        job.bgModel_File.save(model_name + '.hbcp', files.File(handle))

    job.model_order = motif.model_parameters.modelorder
    job.background_Order = motif.model_parameters.bgmodelorder

    job.save()

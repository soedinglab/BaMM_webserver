from os import path
import logging

from ..models import (
    Motifs,
    DbMatch,
    ChIPseq
)
from ..utils import (
    get_job_output_folder,
    run_command
)

from ..commands import (
    get_logo_command,
)
from .commands import (
    get_pwm2bamm_command,
    get_jointprob_command,
)

logger = logging.getLogger(__name__)


def initialize_motifs_compare(job):
    meta_job = job.meta_job
    job_pk = meta_job.pk
    prefix = job.filename_prefix
    iupac_file = path.join(get_job_output_folder(job_pk), prefix + '.iupac')
    with open(iupac_file) as f:
        for i, l in enumerate(f):
            pass
    job.num_motifs = i + 1
    for motif in range(1, (int(job.num_motifs) + 1)):
        motif_obj = Motifs(parent_job=meta_job, job_rank=motif)
        motif_obj.save()


def register_query_motifs(job):
    for motif_no in range(job.num_motifs):
        motif_obj = Motifs(parent_job=job.meta_job, job_rank=motif_no + 1)
        motif_obj.save()


def make_logos(job):
    if job.Motif_Init_File_Format == "MEME":
        run_command(get_pwm2bamm_command(job))
        run_command(get_logo_command(job, order=0))
    if job.Motif_Init_File_Format == "BaMM":
        run_command(get_jointprob_command(job))
        for order in range(min(job.model_order+1, 3)):
            run_command(get_logo_command(job, order))


def add_motif_motif_matches(job):
    job_pk = job.meta_job.pk
    motifs = Motifs.objects.filter(parent_job=job.meta_job)
    prefix = job.filename_prefix
    mmcomp_file = path.join(get_job_output_folder(job_pk), prefix + '.mmcomp')
    with open(mmcomp_file) as handle:
        for line in handle:
            tokens = line.split()
            if len(tokens) > 0:
                # first line is "no matches!" when no hit is found.
                # in this case we want to skip the line
                if tokens[1] != 'matches!':
                    motif_query = motifs.filter(job_rank=tokens[1])[0]
                    matching_models = ChIPseq.objects.filter(
                        motif_db=job.motif_db, filename=tokens[2]
                    )
                    if len(matching_models) != 1:
                        logger.error('database %s inconsistent. Model %s defined but not found',
                                     job.motif_db, tokens[2])
                        assert False
                    target_motif, = matching_models

                    # create relationship
                    rel_obj = DbMatch(
                        motif=motif_query,
                        db_entry=target_motif,
                        p_value=tokens[3],
                        e_value=tokens[4],
                        score=tokens[5],
                        overlap_len=tokens[6]
                    )
                    rel_obj.save()

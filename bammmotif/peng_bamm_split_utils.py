from django.shortcuts import get_object_or_404
from .models import PengJob
from django.core.files import File
from django.conf import settings

def upload_example_fasta_for_peng(job_id):
    peng_job = get_object_or_404(PengJob, pk=job_id)
    out_filename = "ExampleData.fasta"
    with open(settings.EXAMPLE_FASTA) as fh:
        peng_job.fasta_file.save(out_filename, File(fh))
        peng_job.save()

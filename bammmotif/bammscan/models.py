from os import path

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from ..models import JobInfo, MotifDatabase

from ..utils import get_job_input_folder, job_upload_to_input


FORMAT_CHOICES = (
    ('MEME', 'MEME'),
    ('BaMM', 'BaMM'),
)


class BaMMScanJob(models.Model):
    meta_job = models.OneToOneField(JobInfo, on_delete=models.CASCADE,
                                    primary_key=True, editable=False)

    Input_Sequences = models.FileField(upload_to=job_upload_to_input, null=True)
    reverse_Complement = models.BooleanField(default=True)

    num_motifs = models.IntegerField(default=1)
    Motif_InitFile = models.FileField(upload_to=job_upload_to_input, null=True, blank=True)
    Motif_Init_File_Format = models.CharField(max_length=255, choices=FORMAT_CHOICES,
                                              default="MEME")

    model_order = models.PositiveSmallIntegerField(default=4)
    background_Order = models.PositiveSmallIntegerField(default=2)

    # needed for get_core_params compatibility
    Background_Sequences = models.FileField(upload_to=job_upload_to_input, null=True, blank=True)
    num_init_motifs = models.IntegerField(default=10)

    # BaMMScan
    score_Seqset = models.BooleanField(default=True)
    score_Cutoff = models.FloatField(default=0.0001)
    bgModel_File = models.FileField(upload_to=job_upload_to_input, null=True, blank=True)

    # FDR related fields
    FDR = models.BooleanField(default=True)
    m_Fold = models.IntegerField(default=1)
    sampling_Order = models.PositiveSmallIntegerField(default=2)

    # MMcompare related fields
    MMcompare = models.BooleanField(default=False)
    e_value_cutoff = models.DecimalField(default=0.1, max_digits=3, decimal_places=2)
    motif_db = models.ForeignKey(MotifDatabase, null=True, on_delete=models.CASCADE)

    has_bedfile = models.BooleanField(default=False)

    @property
    def cvFold(self):
        return settings.FDR_CV_FOLD

    @property
    def filename_prefix(self):
        file_name = path.basename(self.Motif_InitFile.name)
        prefix, _ = path.splitext(file_name)
        return prefix

    def __str__(self):
        return str(self.meta_job.job_id)

    @property
    def full_motif_file_path(self):
        return path.join(settings.JOB_DIR, str(self.Motif_InitFile))

    @property
    def bamm_init_file(self):
        return self.full_motif_file_path

    @property
    def input_basename(self):
        return path.basename(self.Input_Sequences.name)

    @property
    def motif_basename(self):
        return path.basename(self.Motif_InitFile.name)

    @property
    def bgmodel_basename(self):
        if not self.bgModel_File:
            return None
        else:
            return path.basename(self.bgModel_File.name)

    @property
    def full_motif_bg_file_path(self):
        return path.join(settings.JOB_DIR, str(self.bgModel_File))


@receiver(post_delete, sender=BaMMScanJob)
def delete_job_info(sender, instance, *args, **kwargs):
    if instance.meta_job:
        instance.meta_job.delete()

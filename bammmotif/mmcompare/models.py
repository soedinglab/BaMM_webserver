from os import path
import re

from django.db import models
from django.db.models.signals import post_delete
from django.conf import settings
from django.dispatch import receiver

from ..models import JobInfo, MotifDatabase
from ..utils import file_size_validator


INIT_FORMAT_CHOICES = (
    ('MEME', 'MEME'),
    ('BaMM', 'BaMM'),
)


def job_directory_path_motif(instance, filename):
    return path.join(settings.JOB_DIR_PREFIX, str(instance.meta_job.pk),
                     'Input', str(filename))


class MMcompareJob(models.Model):
    meta_job = models.OneToOneField(JobInfo, on_delete=models.CASCADE, primary_key=True)

    Motif_InitFile = models.FileField(upload_to=job_directory_path_motif, null=True,
                                      validators=[file_size_validator])
    Motif_Init_File_Format = models.CharField(max_length=255, choices=INIT_FORMAT_CHOICES,
                                              default="MEME")
    num_motifs = models.IntegerField(default=1)
    model_order = models.PositiveSmallIntegerField(default=4)
    bgModel_File = models.FileField(upload_to=job_directory_path_motif, null=True, blank=True,
                                    validators=[file_size_validator])
    e_value_cutoff = models.DecimalField(default=0.5, max_digits=3, decimal_places=2)
    motif_db = models.ForeignKey(MotifDatabase, null=True, on_delete=models.CASCADE)

    @property
    def filename_prefix(self):
        file_name = path.basename(self.Motif_InitFile.name)
        prefix, _ = path.splitext(file_name)
        if self.Motif_Init_File_Format == 'BaMM':
            prefix = re.sub('_motif_[0-9]+$', '', prefix)
        return prefix

    @property
    def full_motif_file_path(self):
        return path.join(settings.JOB_DIR, str(self.Motif_InitFile))

    @property
    def full_motif_bg_file_path(self):
        return path.join(settings.JOB_DIR, str(self.bgModel_File))

    @property
    def motif_file_name(self):
        return path.basename(str(self.Motif_InitFile))

    @property
    def mmcompare_from_meme(self):
        return self.Motif_Init_File_Format == 'MEME'

    @property
    def motif_basename(self):
        return path.basename(self.Motif_InitFile.name)

    @property
    def bgmodel_basename(self):
        if not self.bgModel_File:
            return None
        else:
            return path.basename(self.bgModel_File.name)

    def __str__(self):
        return str(self.meta_job.job_id)


@receiver(post_delete, sender=MMcompareJob)
def delete_job_info(sender, instance, *args, **kwargs):
    if instance.meta_job:
        instance.meta_job.delete()

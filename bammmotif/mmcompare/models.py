from os import path

from django.db import models
from django.conf import settings

from bammmotif.models import JobInfo, MotifDatabase


INIT_FORMAT_CHOICES = (
    ('BindingSites', 'BindingSites'),
    ('PWM', 'PWM'),
    ('BaMM', 'BaMM'),
)


def job_directory_path_motif(instance, filename):
    return path.join(settings.JOB_DIR_PREFIX, str(instance.meta_job.pk),
                     'Input', str(filename))


class MMcompareJob(models.Model):
    meta_job = models.OneToOneField(JobInfo, on_delete=models.CASCADE, primary_key=True)

    Motif_InitFile = models.FileField(upload_to=job_directory_path_motif, null=True, blank=True)
    Motif_Init_File_Format = models.CharField(max_length=255, choices=INIT_FORMAT_CHOICES,
                                              default="PWM")
    model_order = models.PositiveSmallIntegerField(default=4)
    bgModel_File = models.FileField(upload_to=job_directory_path_motif, null=True, blank=True)
    p_value_cutoff = models.DecimalField(default=0.01, max_digits=3, decimal_places=2)
    motif_db = models.ForeignKey(MotifDatabase, null=True, on_delete=models.CASCADE)

    @property
    def filename_prefix(self):
        file_name = path.basename(self.Motif_InitFile.name)
        prefix, _ = path.splitext(file_name)
        return prefix

    def __str__(self):
        return str(self.meta_job.job_id)

from os import path

from django.db import models
from django.conf import settings

from ..models import JobInfo, MotifDatabase, PengJob
from ..utils import job_dir_storage as job_fs
from ..utils import job_upload_to_input


FORMAT_CHOICES = (
    ('BindingSites', 'BindingSites'),
    ('PWM', 'PWM'),
    ('BaMM', 'BaMM'),
)

INIT_CHOICES = (
    ('CustomFile', 'CustomFile'),
    ('PEnGmotif', 'PEnGmotif'),
    ('DBFile', 'DBFile'),
)


class BaMMJob(models.Model):
    meta_job = models.OneToOneField(JobInfo, on_delete=models.CASCADE, editable=False,
                                    primary_key=True)
    peng_job = models.ForeignKey(PengJob, editable=False, on_delete=models.CASCADE)
    num_motifs = models.IntegerField(default=1)

    # files
    Input_Sequences = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                       null=True)
    Background_Sequences = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                            null=True, blank=True)
    Motif_Initialization = models.CharField(max_length=255, choices=INIT_CHOICES,
                                            default="PEnGmotif")
    Motif_InitFile = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                      null=True, blank=True)
    Motif_Init_File_Format = models.CharField(max_length=255, choices=FORMAT_CHOICES, default="PWM")
    num_init_motifs = models.IntegerField(default=10)

    # options
    model_order = models.PositiveSmallIntegerField(default=4)
    reverse_Complement = models.BooleanField(default=True)
    extend = models.PositiveSmallIntegerField(default=0)

    # fdr options
    FDR = models.BooleanField(default=True)
    m_Fold = models.IntegerField(default=10)
    sampling_Order = models.PositiveSmallIntegerField(default=2)

    # EM options
    EM = models.BooleanField(default=True)
    q_value = models.DecimalField(default=0.9, max_digits=3, decimal_places=2)

    # scoring options
    score_Seqset = models.BooleanField(default=True)
    score_Cutoff = models.FloatField(default=0.1)
    bgModel_File = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                    null=True, blank=True)

    # advanced options
    background_Order = models.PositiveSmallIntegerField(default=2)
    verbose = models.BooleanField(default=True)

    # MMcompare
    MMcompare = models.BooleanField(default=False)
    e_value_cutoff = models.DecimalField(default=0.01, max_digits=3, decimal_places=2)
    motif_db = models.ForeignKey(MotifDatabase, null=True, on_delete=models.CASCADE)

    @property
    def filename_prefix(self):
        file_name = path.basename(self.Input_Sequences.name)
        prefix, _ = path.splitext(file_name)
        return prefix

    @property
    def full_motif_file_path(self):
        return path.join(settings.JOB_DIR, str(self.Motif_InitFile))

    def __str__(self):
        return str(self.meta_job.pk)

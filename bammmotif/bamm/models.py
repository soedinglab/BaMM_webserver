from os import path

from django.db import models
from django.conf import settings

from ..models import JobInfo, MotifDatabase, PengJob
from ..utils import job_dir_storage as job_fs
from ..utils import (
    job_upload_to_input,
    file_size_validator,
    get_job_output_folder,
)
from ..peng.cmd_modules import ShootPengModule


FORMAT_CHOICES = (
    ('MEME', 'MEME'),
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
    Motif_Init_File_Format = models.CharField(max_length=255, choices=FORMAT_CHOICES, default="MEME")
    num_init_motifs = models.IntegerField(default=10)

    # options
    model_order = models.PositiveSmallIntegerField(default=2)
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
    score_Cutoff = models.FloatField(default=0.001)
    bgModel_File = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                    null=True, blank=True)

    # advanced options
    background_Order = models.PositiveSmallIntegerField(default=2)
    verbose = models.BooleanField(default=True)

    # MMcompare
    MMcompare = models.BooleanField(default=True)
    e_value_cutoff = models.DecimalField(default=0.5, max_digits=3, decimal_places=2)
    motif_db = models.ForeignKey(MotifDatabase, null=True, on_delete=models.CASCADE)

    @property
    def filename_prefix(self):
        file_name = path.basename(self.Input_Sequences.name)
        prefix, _ = path.splitext(file_name)
        return prefix

    def input_basename(self):
        return path.basename(self.Input_Sequences.name)

    @property
    def full_motif_file_path(self):
        return path.join(settings.JOB_DIR, str(self.Motif_InitFile))

    @property
    def bamm_init_file(self):
        return self.Motif_InitFile

    @property
    def meme_output(self):
        return path.join(get_job_output_folder(self.meta_job.pk), 'seeds.meme')

    @property
    def n_threads(self):
        return settings.N_PARALLEL_THREADS

    @property
    def cvFold(self):
        return settings.N_PARALLEL_THREADS

    def __str__(self):
        return str(self.meta_job.pk)


class OneStepBaMMJob(models.Model):

    # general settings
    meta_job = models.OneToOneField(JobInfo, on_delete=models.CASCADE, editable=False,
                                    primary_key=True)

    # shared
    Input_Sequences = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                       null=True, validators=[file_size_validator])
    Background_Sequences = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                            null=True, blank=True, validators=[file_size_validator])
    num_motifs = models.IntegerField(default=1)
    reverse_Complement = models.BooleanField(default=True)
    background_Order = models.PositiveSmallIntegerField(default=2)

    # peng-motif seeding
    temp_dir = models.CharField(max_length=100, null=True,
                                default=ShootPengModule.defaults['temp_dir'])
    pattern_length = models.IntegerField(default=ShootPengModule.defaults['pattern_length'])
    zscore_threshold = models.FloatField(default=ShootPengModule.defaults['zscore_threshold'])
    count_threshold = models.IntegerField(default=ShootPengModule.defaults['count_threshold'])
    objective_function = models.CharField(
        choices=[(choice, choice) for choice in ShootPengModule.objective_functions],
        max_length=50, default=ShootPengModule.defaults['optimization_score'])
    enrich_pseudocount_factor = models.FloatField(
        default=ShootPengModule.defaults['enrich_pseudocount_factor'])
    no_em = models.BooleanField(default=ShootPengModule.defaults['no_em'])
    em_saturation_threshold = models.FloatField(
        default=ShootPengModule.defaults['em_saturation_threshold'])
    em_threshold = models.FloatField(default=ShootPengModule.defaults['em_threshold'])
    em_max_iterations = models.IntegerField(default=ShootPengModule.defaults['em_max_iterations'])
    no_merging = models.BooleanField(default=ShootPengModule.defaults['no_merging'])
    bit_factor_threshold = models.FloatField(
        default=ShootPengModule.defaults['bit_factor_threshold'])
    use_default_pwm = models.BooleanField(default=ShootPengModule.defaults['use_default_pwm'])
    pwm_pseudo_counts = models.IntegerField(default=ShootPengModule.defaults['pwm_pseudo_counts'])
    silent = models.BooleanField(default=ShootPengModule.defaults['silent'])
    max_refined_motifs = models.IntegerField(default=3)

    # patches for shared attributes
    @property
    def fasta_file(self):
        return self.Input_Sequences

    @property
    def bg_sequences(self):
        return self.Background_Sequences

    @property
    def strand(self):
        return 'BOTH' if self.reverse_Complement else 'PLUS'

    @property
    def bg_model_order(self):
        return self.background_Order

    @property
    def cvFold(self):
        return settings.N_PARALLEL_THREADS

    @property
    def n_threads(self):
        return settings.N_PARALLEL_THREADS

    def input_basename(self):
        return path.basename(self.Input_Sequences.name)

    # BaMM related functionality

    # files
    Motif_Initialization = models.CharField(max_length=255, choices=INIT_CHOICES,
                                            default="PEnGmotif")
    Motif_InitFile = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                      null=True, blank=True)
    Motif_Init_File_Format = models.CharField(max_length=255, choices=FORMAT_CHOICES, default="MEME")

    # options
    model_order = models.PositiveSmallIntegerField(default=2)
    extend = models.PositiveSmallIntegerField(default=0)

    # fdr options
    FDR = models.BooleanField(default=True)
    m_Fold = models.IntegerField(default=10)
    sampling_Order = models.PositiveSmallIntegerField(default=2)

    # EM options
    EM = models.BooleanField(default=True)

    # scoring options
    score_Seqset = models.BooleanField(default=True)
    score_Cutoff = models.FloatField(default=0.001)
    bgModel_File = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                    null=True, blank=True)

    # advanced options
    verbose = models.BooleanField(default=True)

    # MMcompare
    MMcompare = models.BooleanField(default=True)
    e_value_cutoff = models.DecimalField(default=0.5, max_digits=3, decimal_places=2)
    motif_db = models.ForeignKey(MotifDatabase, null=True, on_delete=models.CASCADE)

    @property
    def filename_prefix(self):
        file_name = path.basename(self.Input_Sequences.name)
        prefix, _ = path.splitext(file_name)
        return prefix

    @property
    def full_motif_file_path(self):
        return path.join(settings.JOB_DIR, str(self.Motif_InitFile))

    @property
    def full_sequence_file_path(self):
        return path.join(settings.JOB_DIR, str(self.Input_Sequences.path))

    @property
    def meme_output(self):
        return path.join(get_job_output_folder(self.meta_job.pk), 'seeds.meme')

    @property
    def q_value(self):
        # for now set default p-value to 0.5
        return 0.5

    def __str__(self):
        return str(self.meta_job.pk)

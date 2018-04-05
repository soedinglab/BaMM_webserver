from os import path

from django.db import models

from ..models import JobInfo
from .cmd_modules import ShootPengModule

from ..utils import job_dir_storage as job_fs
from ..utils import job_upload_to_input


class PengJob(models.Model):
    meta_job = models.OneToOneField(JobInfo, on_delete=models.CASCADE, editable=False,
                                    primary_key=True)
    num_motifs = models.IntegerField(default=1)
    fasta_file = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                  null=True)
    temp_dir = models.CharField(max_length=100, null=True,
                                default=ShootPengModule.defaults['temp_dir'])
    bg_sequences = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                    null=True, blank=True)
    pattern_length = models.IntegerField(default=ShootPengModule.defaults['pattern_length'])
    zscore_threshold = models.FloatField(default=ShootPengModule.defaults['zscore_threshold'])
    count_threshold = models.IntegerField(default=ShootPengModule.defaults['count_threshold'])
    bg_model_order = models.IntegerField(default=ShootPengModule.defaults['bg_model_order'])

    reverse_Complement = models.BooleanField(default=True)
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
    n_threads = models.IntegerField(default=ShootPengModule.defaults['n_threads'])
    silent = models.BooleanField(default=ShootPengModule.defaults['silent'])

    @property
    def filename_prefix(self):
        file_name = path.basename(self.fasta_file.name)
        prefix, _ = path.splitext(file_name)
        return prefix

    @property
    def strand(self):
        return 'BOTH' if self.reverse_Complement else 'PLUS'

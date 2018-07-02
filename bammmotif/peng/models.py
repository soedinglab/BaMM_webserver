from os import path

from django.db import models
from django.db.models.signals import post_delete
from django.conf import settings
from django.dispatch import receiver

from ..models import JobInfo
from .cmd_modules import ShootPengModule

from ..utils import job_dir_storage as job_fs
from ..utils import (
    job_upload_to_input,
    get_job_output_folder,
    file_size_validator,
)


class PengJob(models.Model):
    meta_job = models.OneToOneField(JobInfo, on_delete=models.CASCADE, editable=False,
                                    primary_key=True)
    num_motifs = models.IntegerField(default=1)
    fasta_file = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                  null=True, validators=[file_size_validator])
    temp_dir = models.CharField(max_length=100, null=True,
                                default=ShootPengModule.defaults['temp_dir'])
    bg_sequences = models.FileField(upload_to=job_upload_to_input, storage=job_fs,
                                    null=True, blank=True, validators=[file_size_validator])
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
    silent = models.BooleanField(default=ShootPengModule.defaults['silent'])

    @property
    def filename_prefix(self):
        file_name = path.basename(self.fasta_file.name)
        prefix, _ = path.splitext(file_name)
        return prefix

    @property
    def strand(self):
        return 'BOTH' if self.reverse_Complement else 'PLUS'

    @property
    def meme_output(self):
        return path.join(get_job_output_folder(self.meta_job.pk), 'seeds.meme')

    @property
    def n_threads(self):
        return settings.N_PARALLEL_THREADS

    # compatibility layer to old BaMM workflow
    @property
    def Background_Sequences(self):
        return self.bg_sequences

    @property
    def Input_Sequences(self):
        return self.fasta_file

    @property
    def background_Order(self):
        return self.bg_model_order

    @property
    def input_basename(self):
        return path.basename(self.fasta_file.name)


@receiver(post_delete, sender=PengJob)
def delete_job_info(sender, instance, *args, **kwargs):
    if instance.meta_job:
        instance.meta_job.delete()

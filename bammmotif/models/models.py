from __future__ import unicode_literals
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
import uuid
import os
from os import path


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

ALPHABET_CHOICES = (
    ('STANDARD', 'STANDARD'),
    ('METHYLIC', 'METHYLIC'),
    ('HYDROXYMETHYLIC', 'HYDROXYMETHYLIC'),
    ('EXTENDED', 'EXTENDED'),
)

MODE_CHOICES = (
    ('Prediction','Prediction'),
    ('Occurrence','Occurrence'),
    ('Compare','Compare')
)

JOB_INFO_MODE_CHOICES = (
    ('peng', 'peng'),
    ('bamm', 'bamm'),
    ('bammscan', 'bammscan'),
    ('mmcompare', 'mmcompare'),
)

JOB_MODE_MAPPING = {
    'peng': 'De-novo discovery',
    'bamm': 'Motif refinement',
    'bammscan': 'Motif scan',
    'mmcompare': 'Motif-Motif comparison',
}


def job_directory_path_new(instance, filename):
    return os.path.join(settings.JOB_DIR_PREFIX, str(instance.job_id),
                        'Input', str(filename))


def job_directory_path_sequence_new(instance, filename):
    f_name = filename.replace("_", "-")
    return os.path.join(settings.JOB_DIR_PREFIX, str(instance.job_id),
                        'Input', str(f_name))

def job_directory_path_motif_new(instance, filename):
    return os.path.join(settings.JOB_DIR_PREFIX, str(instance.job_id),
                        'Input', str(filename))

def job_directory_path_peng_new(instance, filename):
    path_to_job = "/code/media"
    return os.path.join(path_to_job, settings.JOB_DIR_PREFIX, str(instance.job_id), 'Input', str(filename))


def job_directory_path(instance, filename):
    return os.path.join(settings.JOB_DIR_PREFIX, str(instance.job_ID),
                        'Input', str(filename))


def job_directory_path_sequence(instance, filename):
    f_name = filename.replace("_", "-")
    return os.path.join(settings.JOB_DIR_PREFIX, str(instance.job_ID),
                        'Input', str(f_name))

def job_directory_path_motif(instance, filename):
    return os.path.join(settings.JOB_DIR_PREFIX, str(instance.job_ID),
                        'Input', str(filename))


def job_directory_path_peng(instance, filename):
    path_to_job = "/code/media"
    return os.path.join(path_to_job, settings.JOB_DIR_PREFIX, str(instance.job_ID), 'Input', str(filename))

def job_directory_path_peng_meta(instance, filename, intermediate_dir="Input"):
    path = os.path.join(settings.MEDIA_ROOT, str(instance.job_id), intermediate_dir)
    if not os.path.exists(path):
        os.makedirs(path)
    return os.path.join(path, str(filename))


class DbParameter(models.Model):
    param_id = models.AutoField(db_column='param_ID', primary_key=True)  # Field name made lowercase.
    data_source = models.CharField(max_length=100)
    species = models.CharField(max_length=12)
    experiment = models.CharField(max_length=20)
    base_dir = models.CharField(max_length=50)
    motif_init_file_format = models.CharField(max_length=255)
    #alphabet = models.CharField(max_length=12)
    reversecomp = models.IntegerField(db_column='reverseComp')  # Field name made lowercase.
    modelorder = models.IntegerField(db_column='modelOrder')  # Field name made lowercase.
    extend_1 = models.IntegerField()
    extend_2 = models.IntegerField()
    bgmodelorder = models.IntegerField(db_column='bgModelOrder')  # Field name made lowercase.
    em = models.IntegerField(db_column='EM')  # Field name made lowercase.
    #maxemiterations = models.BigIntegerField(db_column='maxEMIterations')  # Field name made lowercase.
    #epsilon = models.FloatField()
    fdr = models.IntegerField(db_column='FDR')  # Field name made lowercase.
    mfold = models.IntegerField(db_column='mFold')  # Field name made lowercase.
    #cvfold = models.IntegerField(db_column='cvFold')  # Field name made lowercase.
    samplingorder = models.IntegerField(db_column='samplingOrder')  # Field name made lowercase.
    #savelogodds = models.IntegerField(db_column='saveLogOdds')  # Field name made lowercase.
    #cgs = models.IntegerField(db_column='CGS')  # Field name made lowercase.
    #maxcgsiterations = models.BigIntegerField(db_column='maxCGSIterations')  # Field name made lowercase.
    #noalphasampling = models.IntegerField(db_column='noAlphaSampling')  # Field name made lowercase.
    
    def __str__(self):
        return self.param_id


class MotifDatabase(models.Model):
    db_id = models.CharField(max_length=100, primary_key=True)
    version = models.CharField(max_length=50)
    organism = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    model_parameters = models.ForeignKey(DbParameter, on_delete=models.CASCADE, null=True)

    @property
    def db_directory(self):
        return path.join(settings.MOTIF_DATABASE_PATH, str(self.db_id))

    @property
    def db_model_directory(self):
        return path.join(self.db_directory, 'models')

    @property
    def relative_db_model_dir(self):
        return path.join(str(self.db_id), 'models')


    def __str__(self):
        return str(self.db_id)


class ChIPseq(models.Model):
    motif_id = models.CharField(max_length=100, primary_key=True)
    filename = models.CharField(max_length=255)
    lab = models.CharField(max_length=100, null=True)
    grant = models.CharField(max_length=100, null=True)
    cell_type = models.CharField(max_length=250, null=True)
    target_name = models.CharField(max_length=100)
    ensembl_target_id = models.CharField(max_length=100, null=True)
    treatment = models.CharField(max_length=100, null=True)
    protocol = models.CharField(max_length=100, null=True)
    pos_seq_file = models.CharField(max_length=120)
    motif_init_file = models.CharField(max_length=255)
    result_location = models.CharField(max_length=100, null=True)
    url = models.URLField(null=True)
    parent = models.ForeignKey(DbParameter, blank=True, null=True, on_delete=models.CASCADE)
    motif_db = models.ForeignKey(MotifDatabase, null=True, on_delete=models.CASCADE)

    # overwrite a previous database field. This patch makes previous code runnable
    @property
    def result_location(self):
        return self.filename
    
    def __str__(self):
        return self.motif_id

    @property
    def model_parameters(self):
        return self.parent

    @property
    def filename_prefix(self):
        prefix, extension = path.splitext(self.filename)
        return prefix


class JobInfo(models.Model):
    # General information about each job is stored here.
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_name = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    mode = models.CharField(max_length=50, default="Prediction", choices=MODE_CHOICES)
    status = models.CharField(max_length=255, default="queueing", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    job_type = models.CharField(max_length=30, null=True, blank=True, choices=JOB_INFO_MODE_CHOICES)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return str(self.job_id)

    @property
    def job_type_display(self):
        return JOB_MODE_MAPPING[self.job_type]


class Motifs(models.Model):
    motif_ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_job = models.ForeignKey(JobInfo, on_delete=models.CASCADE, null=False)
    iupac = models.CharField(max_length=50, null=True, blank=True)
    job_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    length = models.PositiveSmallIntegerField(null=True, blank=True)
    auc = models.FloatField(blank=True, null=True)
    occurrence = models.FloatField(blank=True, null=True)
    db_match = models.ManyToManyField('ChIPseq', through='DbMatch', blank=True)

    def __str__(self):
        return self.motif_ID


class DbMatch(models.Model):
    match_ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    motif = models.ForeignKey('Motifs', on_delete=models.CASCADE)
    db_entry = models.ForeignKey('ChIPseq', on_delete=models.CASCADE)
    p_value = models.FloatField(default=0.0)
    e_value = models.FloatField(default=0.0)
    score = models.FloatField(default=0.0)
    overlap_len = models.IntegerField(default=0)

    def __str__(self):
        return self.match_ID


class JobSession(models.Model):
    session_key = models.CharField(max_length=100, null=True)
    job = models.ForeignKey(JobInfo, on_delete=models.CASCADE)
    creation_time = models.DateTimeField(default=timezone.now)

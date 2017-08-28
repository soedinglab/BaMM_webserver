from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime
import uuid
import os

FORMAT_CHOICES = (
    ('BindingSites', 'BindingSites'),
    ('PWM', 'PWM'), 
    ('BaMM','BaMM'),
)

INIT_CHOICES = (
    ('Custom File','Custom File'),
    ('PEnGmotif','PEnGmotif'),
    ('DB File','DB File'),
)

ALPHABET_CHOICES = (
    ('STANDARD', 'STANDARD'),
    ('METHYLIC', 'METHYLIC'),
    ('HYDROXYMETHYLIC', 'HYDROXYMETHYLIC'),
    ('EXTENDED', 'EXTENDED'),
)

MODE_CHOICES = (
    ('Prediction','Prediction'),
    ('Occurrence','Occurrence')
)

def job_directory_path(instance, filename):
   	return '{0}/Input/{1}'.format(instance.job_ID, filename)

class Job(models.Model):
    # general info
    job_ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_name=models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField( default=datetime.datetime.now)
    mode = models.CharField(max_length=50, default="Predicition", choices=MODE_CHOICES) 
    status = models.CharField(max_length=255, default="not initialized", null=True, blank=True)
    num_motifs = models.IntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
        
    # files  
    Input_Sequences = models.FileField(upload_to=job_directory_path, null=True)
    Background_Sequences = models.FileField(upload_to=job_directory_path, null=True, blank=True)
    Intensity_File = models.FileField(upload_to=job_directory_path , null=True, blank=True)
    Motif_Initialization = models.CharField(max_length=255, choices=INIT_CHOICES, default="PEnGmotif")
    Motif_InitFile = models.FileField(upload_to=job_directory_path, null=True, blank=True)
    Motif_Init_File_Format = models.CharField(max_length=255, choices=FORMAT_CHOICES, default="PWM")
    num_init_motifs = models.IntegerField(default = 100)

    # options
    model_Order =models.PositiveSmallIntegerField(default=4)
    reverse_Complement = models.BooleanField(default=True)
    extend_1 = models.PositiveSmallIntegerField(default=10)
    extend_2 = models.PositiveSmallIntegerField(default=10)

    # fdr options
    FDR = models.BooleanField(default=True)
    m_Fold = models.IntegerField(default=5)
    cv_Fold = models.IntegerField(default=5)
    sampling_Order = models.PositiveSmallIntegerField(default=2)
    save_LogOdds = models.BooleanField(default=False)

    # CGS options
    CGS = models.BooleanField(default=False)
    max_CGS_Iterations = models.BigIntegerField(default=10e5)
    no_Alpha_Sampling = models.BooleanField( default=True)

    # EM options
    EM = models.BooleanField(default=True)    
    epsilon = models.DecimalField(default=0.001, max_digits=5, decimal_places=4)
    q_value = models.DecimalField(default=0.9, max_digits=3, decimal_places=2)
    max_EM_Iterations = models.BigIntegerField(default=10e5)
    no_Alpha_Optimization = models.BooleanField(default=True)

    # scoring options
    score_Seqset = models.BooleanField(default=False)
    score_Cutoff = models.FloatField(default=3.0)
    bgModel_File = models.FileField( upload_to=job_directory_path, null=True, blank=True)

    # advanced options
    alphabet = models.CharField(max_length=255, choices=ALPHABET_CHOICES, default="STANDARD")
    background_Order = models.PositiveSmallIntegerField(default=2)
    verbose = models.BooleanField(default=True)
    save_BaMMs = models.BooleanField(default=True)
    save_BgModel = models.BooleanField(default=True)
    p_value_cutoff = models.DecimalField(default=0.01, max_digits=3,decimal_places=2)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.job_ID

    def Output_filename(self):
        return os.path.splitext(os.path.basename(self.Input_Sequences.name))[0]
        
    def Inputseq_filename(self):
        return os.path.basename(self.Input_Sequences.name)
        
    def Background_filename(self):
        return os.path.basename(self.Background_Sequences.name)

    def Intensity_filename(self):
        return os.path.basename(self.Intensity_File.name)

    def MotifInit_filename(self):
        return os.path.basename(self.Motif_InitFile.name)


class DbParameter(models.Model):
    param_id = models.SmallIntegerField(db_column='param_ID', primary_key=True)  # Field name made lowercase.
    data_source = models.CharField(max_length=12)
    species = models.CharField(max_length=12)
    experiment = models.CharField(max_length=20)
    base_dir = models.CharField(max_length=50)
    motif_init_file_format = models.CharField(max_length=255)
    alphabet = models.CharField(max_length=12)
    reversecomp = models.IntegerField(db_column='reverseComp')  # Field name made lowercase.
    modelorder = models.IntegerField(db_column='modelOrder')  # Field name made lowercase.
    extend_1 = models.IntegerField()
    extend_2 = models.IntegerField()
    bgmodelorder = models.IntegerField(db_column='bgModelOrder')  # Field name made lowercase.
    em = models.IntegerField(db_column='EM')  # Field name made lowercase.
    maxemiterations = models.BigIntegerField(db_column='maxEMIterations')  # Field name made lowercase.
    epsilon = models.FloatField()
    fdr = models.IntegerField(db_column='FDR')  # Field name made lowercase.
    mfold = models.IntegerField(db_column='mFold')  # Field name made lowercase.
    cvfold = models.IntegerField(db_column='cvFold')  # Field name made lowercase.
    samplingorder = models.IntegerField(db_column='samplingOrder')  # Field name made lowercase.
    savelogodds = models.IntegerField(db_column='saveLogOdds')  # Field name made lowercase.
    cgs = models.IntegerField(db_column='CGS')  # Field name made lowercase.
    maxcgsiterations = models.BigIntegerField(db_column='maxCGSIterations')  # Field name made lowercase.
    noalphasampling = models.IntegerField(db_column='noAlphaSampling')  # Field name made lowercase.

    
    def __str__(self):
        return self.param_id

class ChIPseq(models.Model):
    db_public_id = models.UUIDField(db_column='db_public_ID', primary_key=True, default=uuid.uuid4, editable=False)  # Field name made lowercase.
    filename = models.CharField(max_length=255)
    lab = models.CharField(max_length=12)
    grant = models.CharField(max_length=12)
    cell_type = models.CharField(max_length=20)
    target_name = models.CharField(max_length=12)
    ensembl_target_id = models.CharField(max_length=15)
    treatment = models.CharField(max_length=25)
    protocol = models.CharField(max_length=15)
    pos_seq_file = models.CharField(max_length=120)
    motif_init_file = models.CharField(max_length=255)
    result_location = models.CharField(max_length=80)
    parent = models.ForeignKey(DbParameter, blank=True, null=True, on_delete=models.CASCADE)

    
    def __str__(self):
        return self.db_public_id

class Motifs(models.Model):
    motif_ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_job = models.ForeignKey(Job, on_delete=models.CASCADE, null=False)
    iupac = models.CharField(max_length=50, null=True, blank=True)
    job_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    length = models.PositiveSmallIntegerField(null=True, blank=True)
    auc = models.FloatField(blank=True, null=True)
    occurrence = models.FloatField(blank=True, null=True)
    db_match = models.ManyToManyField('ChIPseq', through='DbMatch', blank=True)

    
    def __str__(self):
        return self.motif_ID

class DbMatch(models.Model):
    match_ID     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    motif        = models.ForeignKey('Motifs')
    db_entry     = models.ForeignKey('ChIPseq')
    p_value      = models.FloatField(default=0.0)
    e_value      = models.FloatField(default=0.0)
    score        = models.FloatField(default=0.0)
    overlap_len  = models.IntegerField(default=0)

    def __str__(self):
        return self.match_ID

from __future__ import unicode_literals
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime
import uuid
import os
from .command_line import ShootPengModule

FORMAT_CHOICES = (
    ('BindingSites', 'BindingSites'),
    ('PWM', 'PWM'), 
    ('BaMM','BaMM'),
)

INIT_CHOICES = (
    ('CustomFile','CustomFile'),
    ('PEnGmotif','PEnGmotif'),
    ('DBFile','DBFile'),
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
)

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


class MotifDatabase(models.Model):
    db_id = models.CharField(max_length=100, primary_key=True)
    version = models.CharField(max_length=50)
    organism = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.db_id)


class Job(models.Model):
    # general info
    job_ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_name=models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField( default=datetime.datetime.now)
    mode = models.CharField(max_length=50, default="Prediction", choices=MODE_CHOICES) 
    status = models.CharField(max_length=255, default="queueing", null=True, blank=True)
    num_motifs = models.IntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
        
    # files  
    Input_Sequences = models.FileField(upload_to=job_directory_path_sequence, null=True)
    Background_Sequences = models.FileField(upload_to=job_directory_path_sequence, null=True, blank=True)
    #Intensity_File = models.FileField(upload_to=job_directory_path , null=True, blank=True)
    Motif_Initialization = models.CharField(max_length=255, choices=INIT_CHOICES, default="PEnGmotif")
    Motif_InitFile = models.FileField(upload_to=job_directory_path_motif, null=True, blank=True)
    Motif_Init_File_Format = models.CharField(max_length=255, choices=FORMAT_CHOICES, default="PWM")
    num_init_motifs = models.IntegerField(default = 10)

    # options
    model_Order =models.PositiveSmallIntegerField(default=4)
    reverse_Complement = models.BooleanField(default=True)
    extend = models.PositiveSmallIntegerField(default=0)
    #extend_2 = models.PositiveSmallIntegerField(default=0)

    # fdr options
    FDR = models.BooleanField(default=True)
    m_Fold = models.IntegerField(default=5)
    #cv_Fold = models.IntegerField(default=5)
    sampling_Order = models.PositiveSmallIntegerField(default=2)
    #save_LogOdds = models.BooleanField(default=False)

    # CGS options
    #CGS = models.BooleanField(default=False)
    #max_CGS_Iterations = models.BigIntegerField(default=10e5)
    #no_Alpha_Sampling = models.BooleanField( default=True)

    # EM options
    EM = models.BooleanField(default=True)    
    #epsilon = models.DecimalField(default=0.001, max_digits=5, decimal_places=4)
    q_value = models.DecimalField(default=0.9, max_digits=3, decimal_places=2)
    #max_EM_Iterations = models.BigIntegerField(default=10e5)
    #no_Alpha_Optimization = models.BooleanField(default=True)

    # scoring options
    score_Seqset = models.BooleanField(default=True)
    score_Cutoff = models.FloatField(default=0.1)
    bgModel_File = models.FileField( upload_to=job_directory_path_motif, null=True, blank=True)

    # advanced options
    #alphabet = models.CharField(max_length=255, choices=ALPHABET_CHOICES, default="STANDARD")
    background_Order = models.PositiveSmallIntegerField(default=2)
    verbose = models.BooleanField(default=True)
    #save_BaMMs = models.BooleanField(default=True)
    #save_BgModel = models.BooleanField(default=True)

    # MMcompare
    MMcompare = models.BooleanField(default=False)
    p_value_cutoff = models.DecimalField(default=0.01, max_digits=3, decimal_places=2)
    motif_db = models.ForeignKey(MotifDatabase, null=True, on_delete=models.CASCADE)
    
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


class PengJob_deprecated(models.Model):
    # general info
    job_ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_name = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField( default=datetime.datetime.now)
    mode = models.CharField(max_length=50, default="Prediction", choices=MODE_CHOICES)
    status = models.CharField(max_length=255, default="not initialized", null=True, blank=True)
    num_motifs = models.IntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    complete = models.BooleanField(default=False)

    # Peng specific
    fasta_file = models.FileField(upload_to=job_directory_path_peng, null=True)
    meme_output = models.CharField(default=ShootPengModule.defaults['meme_output'], max_length=150)
    json_output = models.CharField(default=ShootPengModule.defaults['json_output'], max_length=150)
    temp_dir = models.CharField(max_length=100, null=True, default=ShootPengModule.defaults['temp_dir'])
    bg_sequences = models.FileField(upload_to=job_directory_path_peng, null=True, blank=True)
    pattern_length = models.IntegerField(default=ShootPengModule.defaults['pattern_length'])
    zscore_threshold = models.FloatField(default=ShootPengModule.defaults['zscore_threshold'])
    count_threshold = models.IntegerField(default=ShootPengModule.defaults['count_threshold'])
    bg_model_order = models.IntegerField(default=ShootPengModule.defaults['bg_model_order'])
    strand = models.CharField(max_length=5, default="BOTH")
    objective_function = models.CharField(max_length=50, default=ShootPengModule.defaults['iupac_optimization_score'])
    enrich_pseudocount_factor = models.FloatField(default=ShootPengModule.defaults['enrich_pseudocount_factor'])
    no_em = models.BooleanField(default=ShootPengModule.defaults['no_em'])
    em_saturation_threshold = models.FloatField(default=ShootPengModule.defaults['em_saturation_threshold'])
    em_threshold = models.FloatField(default=ShootPengModule.defaults['em_threshold'])
    em_max_iterations = models.IntegerField(default=ShootPengModule.defaults['em_max_iterations'])
    no_merging = models.BooleanField(default=ShootPengModule.defaults['no-merging'])
    bit_factor_threshold = models.FloatField(default=ShootPengModule.defaults['bit_factor_threshold'])
    use_default_pwm = models.BooleanField(default=ShootPengModule.defaults['use_default_pwm'])
    pwm_pseudo_counts = models.IntegerField(default=ShootPengModule.defaults['pwm_pseudo_counts'])
    n_threads = models.IntegerField(default=ShootPengModule.defaults['n_threads'])
    silent = models.BooleanField(default=ShootPengModule.defaults['silent'])


    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return str(self.job_ID)

#    def Output_filename(self):
#        return os.path.splitext(os.path.basename(self.Input_Sequences.name))[0]
#
#    def Inputseq_filename(self):
#        return os.path.basename(self.Input_Sequences.name)
#
#    def Background_filename(self):
#        return os.path.basename(self.Background_Sequences.name)
#
#    def Intensity_filename(self):
#        return os.path.basename(self.Intensity_File.name)
#
#    def MotifInit_filename(self):
#        return os.path.basename(self.Motif_InitFile.name)





class DbParameter(models.Model):
    param_id = models.SmallIntegerField(db_column='param_ID', primary_key=True)  # Field name made lowercase.
    data_source = models.CharField(max_length=12)
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
    db_id = models.ForeignKey(MotifDatabase, null=True, on_delete=models.CASCADE)
    
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
    motif        = models.ForeignKey('Motifs', on_delete=models.CASCADE)
    db_entry     = models.ForeignKey('ChIPseq', on_delete=models.CASCADE)
    p_value      = models.FloatField(default=0.0)
    e_value      = models.FloatField(default=0.0)
    score        = models.FloatField(default=0.0)
    overlap_len  = models.IntegerField(default=0)

    def __str__(self):
        return self.match_ID


class JobInfo(models.Model):
    # General information about each job is stored here.
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_name = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    mode = models.CharField(max_length=50, default="Prediction", choices=MODE_CHOICES)
    status = models.CharField(max_length=255, default="queueing", null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    complete = models.BooleanField(default=False)
    job_type = models.CharField(max_length=30, null=True, blank=True, choices=JOB_INFO_MODE_CHOICES)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return str(self.job_id)

class Peng(models.Model):
    # Peng specific
    #job_id = models.ForeignKey(JobMeta, on_delete=models.CASCADE, editable=False, primary_key=True)
    job_id = models.OneToOneField(JobInfo, on_delete=models.CASCADE, editable=False, primary_key=True)
    num_motifs = models.IntegerField(default=1)
    fasta_file = models.FileField(upload_to=job_directory_path_peng_meta, null=True)
    meme_output = models.CharField(default=ShootPengModule.defaults['meme_output'], max_length=150)
    json_output = models.CharField(default=ShootPengModule.defaults['json_output'], max_length=150)
    temp_dir = models.CharField(max_length=100, null=True, default=ShootPengModule.defaults['temp_dir'])
    bg_sequences = models.FileField(upload_to=job_directory_path_peng, null=True, blank=True)
    pattern_length = models.IntegerField(default=ShootPengModule.defaults['pattern_length'])
    zscore_threshold = models.FloatField(default=ShootPengModule.defaults['zscore_threshold'])
    count_threshold = models.IntegerField(default=ShootPengModule.defaults['count_threshold'])
    bg_model_order = models.IntegerField(default=ShootPengModule.defaults['bg_model_order'])
    strand = models.CharField(max_length=5, default="BOTH")
    objective_function = models.CharField(max_length=50, default=ShootPengModule.defaults['iupac_optimization_score'])
    enrich_pseudocount_factor = models.FloatField(default=ShootPengModule.defaults['enrich_pseudocount_factor'])
    no_em = models.BooleanField(default=ShootPengModule.defaults['no_em'])
    em_saturation_threshold = models.FloatField(default=ShootPengModule.defaults['em_saturation_threshold'])
    em_threshold = models.FloatField(default=ShootPengModule.defaults['em_threshold'])
    em_max_iterations = models.IntegerField(default=ShootPengModule.defaults['em_max_iterations'])
    no_merging = models.BooleanField(default=ShootPengModule.defaults['no-merging'])
    bit_factor_threshold = models.FloatField(default=ShootPengModule.defaults['bit_factor_threshold'])
    use_default_pwm = models.BooleanField(default=ShootPengModule.defaults['use_default_pwm'])
    pwm_pseudo_counts = models.IntegerField(default=ShootPengModule.defaults['pwm_pseudo_counts'])
    n_threads = models.IntegerField(default=ShootPengModule.defaults['n_threads'])
    silent = models.BooleanField(default=ShootPengModule.defaults['silent'])


    class Meta:
        pass

    def __str__(self):
        return "peng_" + str(self.job_id)

    def __eq__(self, obj):
        if isinstance(obj, Peng):
            return str(obj) == self.__str__()
        elif (obj, str):
            return obj == self.__str__()
        return False

class Bamm(models.Model):
    job_id = models.OneToOneField(JobInfo, on_delete=models.CASCADE, editable=False, primary_key=True)
    num_motifs = models.IntegerField(default=1)

    # files
    Input_Sequences = models.FileField(upload_to=job_directory_path_sequence_new, null=True)
    Background_Sequences = models.FileField(upload_to=job_directory_path_sequence_new, null=True, blank=True)
    #Intensity_File = models.FileField(upload_to=job_directory_path , null=True, blank=True)
    Motif_Initialization = models.CharField(max_length=255, choices=INIT_CHOICES, default="PEnGmotif")
    Motif_InitFile = models.FileField(upload_to=job_directory_path_motif_new, null=True, blank=True)
    Motif_Init_File_Format = models.CharField(max_length=255, choices=FORMAT_CHOICES, default="PWM")
    num_init_motifs = models.IntegerField(default = 10)

    # options
    model_Order =models.PositiveSmallIntegerField(default=4)
    reverse_Complement = models.BooleanField(default=True)
    extend = models.PositiveSmallIntegerField(default=0)
    #extend_2 = models.PositiveSmallIntegerField(default=0)

    # fdr options
    FDR = models.BooleanField(default=True)
    m_Fold = models.IntegerField(default=5)
    #cv_Fold = models.IntegerField(default=5)
    sampling_Order = models.PositiveSmallIntegerField(default=2)
    #save_LogOdds = models.BooleanField(default=False)

    # CGS options
    #CGS = models.BooleanField(default=False)
    #max_CGS_Iterations = models.BigIntegerField(default=10e5)
    #no_Alpha_Sampling = models.BooleanField( default=True)

    # EM options
    EM = models.BooleanField(default=True)
    #epsilon = models.DecimalField(default=0.001, max_digits=5, decimal_places=4)
    q_value = models.DecimalField(default=0.9, max_digits=3, decimal_places=2)
    #max_EM_Iterations = models.BigIntegerField(default=10e5)
    #no_Alpha_Optimization = models.BooleanField(default=True)

    # scoring options
    score_Seqset = models.BooleanField(default=True)
    score_Cutoff = models.FloatField(default=0.1)
    bgModel_File = models.FileField( upload_to=job_directory_path_motif_new, null=True, blank=True)

    # advanced options
    #alphabet = models.CharField(max_length=255, choices=ALPHABET_CHOICES, default="STANDARD")
    background_Order = models.PositiveSmallIntegerField(default=2)
    verbose = models.BooleanField(default=True)
    #save_BaMMs = models.BooleanField(default=True)
    #save_BgModel = models.BooleanField(default=True)

    # MMcompare
    MMcompare = models.BooleanField(default=False)
    p_value_cutoff = models.DecimalField(default=0.01, max_digits=3, decimal_places=2)

    #class Meta:
    #    ordering = ['-created_at']

    def __str__(self):
        return str(self.job_id)

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


class Motifs_new(models.Model):
    motif_ID = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent_job = models.ForeignKey(Bamm, on_delete=models.CASCADE, null=False)
    iupac = models.CharField(max_length=50, null=True, blank=True)
    job_rank = models.PositiveSmallIntegerField(null=True, blank=True)
    length = models.PositiveSmallIntegerField(null=True, blank=True)
    auc = models.FloatField(blank=True, null=True)
    occurrence = models.FloatField(blank=True, null=True)
    db_match = models.ManyToManyField('ChIPseq', through='DbMatch_new', blank=True)


    def __str__(self):
        return self.motif_ID

class DbMatch_new(models.Model):
    match_ID     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    motif        = models.ForeignKey('Motifs_new', on_delete=models.CASCADE)
    db_entry     = models.ForeignKey('ChIPseq', on_delete=models.CASCADE)
    p_value      = models.FloatField(default=0.0)
    e_value      = models.FloatField(default=0.0)
    score        = models.FloatField(default=0.0)
    overlap_len  = models.IntegerField(default=0)

    def __str__(self):
        return self.match_ID

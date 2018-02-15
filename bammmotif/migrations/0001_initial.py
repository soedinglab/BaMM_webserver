# Generated by Django 2.0.2 on 2018-02-14 22:56

import bammmotif.mmcompare.models
import bammmotif.utils.misc
import datetime
from django.conf import settings
import django.core.files.storage
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChIPseq',
            fields=[
                ('motif_id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('filename', models.CharField(max_length=255)),
                ('lab', models.CharField(max_length=100, null=True)),
                ('grant', models.CharField(max_length=100, null=True)),
                ('cell_type', models.CharField(max_length=250, null=True)),
                ('target_name', models.CharField(max_length=100)),
                ('ensembl_target_id', models.CharField(max_length=100, null=True)),
                ('treatment', models.CharField(max_length=100, null=True)),
                ('protocol', models.CharField(max_length=100, null=True)),
                ('pos_seq_file', models.CharField(max_length=120)),
                ('motif_init_file', models.CharField(max_length=255)),
                ('url', models.URLField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DbMatch',
            fields=[
                ('match_ID', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('p_value', models.FloatField(default=0.0)),
                ('e_value', models.FloatField(default=0.0)),
                ('score', models.FloatField(default=0.0)),
                ('overlap_len', models.IntegerField(default=0)),
                ('db_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bammmotif.ChIPseq')),
            ],
        ),
        migrations.CreateModel(
            name='DbParameter',
            fields=[
                ('param_id', models.AutoField(db_column='param_ID', primary_key=True, serialize=False)),
                ('data_source', models.CharField(max_length=100)),
                ('species', models.CharField(max_length=12)),
                ('experiment', models.CharField(max_length=20)),
                ('base_dir', models.CharField(max_length=50)),
                ('motif_init_file_format', models.CharField(max_length=255)),
                ('reversecomp', models.IntegerField(db_column='reverseComp')),
                ('modelorder', models.IntegerField(db_column='modelOrder')),
                ('extend_1', models.IntegerField()),
                ('extend_2', models.IntegerField()),
                ('bgmodelorder', models.IntegerField(db_column='bgModelOrder')),
                ('em', models.IntegerField(db_column='EM')),
                ('fdr', models.IntegerField(db_column='FDR')),
                ('mfold', models.IntegerField(db_column='mFold')),
                ('samplingorder', models.IntegerField(db_column='samplingOrder')),
            ],
        ),
        migrations.CreateModel(
            name='JobInfo',
            fields=[
                ('job_id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('job_name', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(default=datetime.datetime.now)),
                ('mode', models.CharField(choices=[('Prediction', 'Prediction'), ('Occurrence', 'Occurrence'), ('Compare', 'Compare')], default='Prediction', max_length=50)),
                ('status', models.CharField(blank=True, default='queueing', max_length=255, null=True)),
                ('complete', models.BooleanField(default=False)),
                ('job_type', models.CharField(blank=True, choices=[('peng', 'peng'), ('bamm', 'bamm'), ('bammscan', 'bammscan'), ('mmcompare', 'mmcompare')], max_length=30, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MotifDatabase',
            fields=[
                ('db_id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('version', models.CharField(max_length=50)),
                ('organism', models.CharField(max_length=100)),
                ('display_name', models.CharField(max_length=100)),
                ('model_parameters', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bammmotif.DbParameter')),
            ],
        ),
        migrations.CreateModel(
            name='Motifs',
            fields=[
                ('motif_ID', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('iupac', models.CharField(blank=True, max_length=50, null=True)),
                ('job_rank', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('length', models.PositiveSmallIntegerField(blank=True, null=True)),
                ('auc', models.FloatField(blank=True, null=True)),
                ('occurrence', models.FloatField(blank=True, null=True)),
                ('db_match', models.ManyToManyField(blank=True, through='bammmotif.DbMatch', to='bammmotif.ChIPseq')),
            ],
        ),
        migrations.CreateModel(
            name='BaMMJob',
            fields=[
                ('meta_job', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='bammmotif.JobInfo')),
                ('num_motifs', models.IntegerField(default=1)),
                ('Input_Sequences', models.FileField(null=True, storage=django.core.files.storage.FileSystemStorage(location='/code/media/'), upload_to=bammmotif.utils.misc.job_upload_to_input)),
                ('Background_Sequences', models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='/code/media/'), upload_to=bammmotif.utils.misc.job_upload_to_input)),
                ('Motif_Initialization', models.CharField(choices=[('CustomFile', 'CustomFile'), ('PEnGmotif', 'PEnGmotif'), ('DBFile', 'DBFile')], default='PEnGmotif', max_length=255)),
                ('Motif_InitFile', models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='/code/media/'), upload_to=bammmotif.utils.misc.job_upload_to_input)),
                ('Motif_Init_File_Format', models.CharField(choices=[('BindingSites', 'BindingSites'), ('PWM', 'PWM'), ('BaMM', 'BaMM')], default='PWM', max_length=255)),
                ('num_init_motifs', models.IntegerField(default=10)),
                ('model_order', models.PositiveSmallIntegerField(default=4)),
                ('reverse_Complement', models.BooleanField(default=True)),
                ('extend', models.PositiveSmallIntegerField(default=0)),
                ('FDR', models.BooleanField(default=True)),
                ('m_Fold', models.IntegerField(default=10)),
                ('sampling_Order', models.PositiveSmallIntegerField(default=2)),
                ('EM', models.BooleanField(default=True)),
                ('q_value', models.DecimalField(decimal_places=2, default=0.9, max_digits=3)),
                ('score_Seqset', models.BooleanField(default=True)),
                ('score_Cutoff', models.FloatField(default=0.1)),
                ('bgModel_File', models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='/code/media/'), upload_to=bammmotif.utils.misc.job_upload_to_input)),
                ('background_Order', models.PositiveSmallIntegerField(default=2)),
                ('verbose', models.BooleanField(default=True)),
                ('MMcompare', models.BooleanField(default=False)),
                ('p_value_cutoff', models.DecimalField(decimal_places=2, default=0.01, max_digits=3)),
                ('motif_db', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bammmotif.MotifDatabase')),
            ],
        ),
        migrations.CreateModel(
            name='BaMMScanJob',
            fields=[
                ('meta_job', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='bammmotif.JobInfo')),
                ('Input_Sequences', models.FileField(null=True, upload_to=bammmotif.utils.misc.job_upload_to_input)),
                ('reverse_Complement', models.BooleanField(default=True)),
                ('num_motifs', models.IntegerField(default=1)),
                ('Motif_InitFile', models.FileField(blank=True, null=True, upload_to=bammmotif.utils.misc.job_upload_to_input)),
                ('Motif_Init_File_Format', models.CharField(choices=[('BindingSites', 'BindingSites'), ('PWM', 'PWM'), ('BaMM', 'BaMM')], default='PWM', max_length=255)),
                ('model_order', models.PositiveSmallIntegerField(default=4)),
                ('background_Order', models.PositiveSmallIntegerField(default=2)),
                ('Background_Sequences', models.FileField(blank=True, null=True, upload_to=bammmotif.utils.misc.job_upload_to_input)),
                ('num_init_motifs', models.IntegerField(default=10)),
                ('score_Seqset', models.BooleanField(default=True)),
                ('score_Cutoff', models.FloatField(default=0.1)),
                ('bgModel_File', models.FileField(blank=True, null=True, upload_to=bammmotif.utils.misc.job_upload_to_input)),
                ('FDR', models.BooleanField(default=True)),
                ('m_Fold', models.IntegerField(default=10)),
                ('sampling_Order', models.PositiveSmallIntegerField(default=2)),
                ('MMcompare', models.BooleanField(default=False)),
                ('p_value_cutoff', models.DecimalField(decimal_places=2, default=0.01, max_digits=3)),
                ('motif_db', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bammmotif.MotifDatabase')),
            ],
        ),
        migrations.CreateModel(
            name='MMcompareJob',
            fields=[
                ('meta_job', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='bammmotif.JobInfo')),
                ('Motif_InitFile', models.FileField(blank=True, null=True, upload_to=bammmotif.mmcompare.models.job_directory_path_motif)),
                ('Motif_Init_File_Format', models.CharField(choices=[('BindingSites', 'BindingSites'), ('PWM', 'PWM'), ('BaMM', 'BaMM')], default='PWM', max_length=255)),
                ('num_motifs', models.IntegerField(default=1)),
                ('model_order', models.PositiveSmallIntegerField(default=4)),
                ('bgModel_File', models.FileField(blank=True, null=True, upload_to=bammmotif.mmcompare.models.job_directory_path_motif)),
                ('p_value_cutoff', models.DecimalField(decimal_places=2, default=0.01, max_digits=3)),
                ('motif_db', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bammmotif.MotifDatabase')),
            ],
        ),
        migrations.CreateModel(
            name='PengJob',
            fields=[
                ('meta_job', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='bammmotif.JobInfo')),
                ('num_motifs', models.IntegerField(default=1)),
                ('fasta_file', models.FileField(null=True, storage=django.core.files.storage.FileSystemStorage(location='/code/media/'), upload_to=bammmotif.utils.misc.job_upload_to_input)),
                ('meme_output', models.CharField(default='out.meme', max_length=150)),
                ('json_output', models.CharField(default='out.json', max_length=150)),
                ('temp_dir', models.CharField(default='temp', max_length=100, null=True)),
                ('bg_sequences', models.FileField(blank=True, null=True, storage=django.core.files.storage.FileSystemStorage(location='/code/media/'), upload_to=bammmotif.utils.misc.job_upload_to_input)),
                ('pattern_length', models.IntegerField(default=10)),
                ('zscore_threshold', models.FloatField(default=10)),
                ('count_threshold', models.IntegerField(default=5)),
                ('bg_model_order', models.IntegerField(default=2)),
                ('strand', models.CharField(default='BOTH', max_length=5)),
                ('objective_function', models.CharField(choices=[('LOGPVAL', 'LOGPVAL'), ('MUTUAL_INFO', 'MUTUAL_INFO'), ('ENRICHMENT', 'ENRICHMENT')], default='MUTUAL_INFO', max_length=50)),
                ('enrich_pseudocount_factor', models.FloatField(default=0.005)),
                ('no_em', models.BooleanField(default=False)),
                ('em_saturation_threshold', models.FloatField(default=10000.0)),
                ('em_threshold', models.FloatField(default=0.08)),
                ('em_max_iterations', models.IntegerField(default=20)),
                ('no_merging', models.BooleanField(default=False)),
                ('bit_factor_threshold', models.FloatField(default=0.4)),
                ('use_default_pwm', models.BooleanField(default=False)),
                ('pwm_pseudo_counts', models.IntegerField(default=10)),
                ('n_threads', models.IntegerField(default=1)),
                ('silent', models.BooleanField(default=True)),
            ],
        ),
        migrations.AddField(
            model_name='motifs',
            name='parent_job',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bammmotif.JobInfo'),
        ),
        migrations.AddField(
            model_name='jobinfo',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='dbmatch',
            name='motif',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bammmotif.Motifs'),
        ),
        migrations.AddField(
            model_name='chipseq',
            name='motif_db',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='bammmotif.MotifDatabase'),
        ),
        migrations.AddField(
            model_name='chipseq',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bammmotif.DbParameter'),
        ),
        migrations.AddField(
            model_name='bammjob',
            name='peng_job',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='bammmotif.PengJob'),
        ),
    ]
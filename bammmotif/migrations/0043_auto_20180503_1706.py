# Generated by Django 2.0.3 on 2018-05-03 17:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bammmotif', '0042_remove_onestepbammjob_bgmodel_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bammjob',
            name='Motif_Init_File_Format',
            field=models.CharField(choices=[('MEME', 'MEME'), ('BaMM', 'BaMM')], default='MEME', max_length=255),
        ),
        migrations.AlterField(
            model_name='onestepbammjob',
            name='Motif_Init_File_Format',
            field=models.CharField(choices=[('MEME', 'MEME'), ('BaMM', 'BaMM')], default='MEME', max_length=255),
        ),
    ]

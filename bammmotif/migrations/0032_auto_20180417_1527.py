# Generated by Django 2.0.3 on 2018-04-17 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bammmotif', '0031_auto_20180417_0507'),
    ]

    operations = [
        migrations.AlterField(
            model_name='onestepbammjob',
            name='pattern_length',
            field=models.IntegerField(default=8),
        ),
        migrations.AlterField(
            model_name='pengjob',
            name='pattern_length',
            field=models.IntegerField(default=8),
        ),
    ]

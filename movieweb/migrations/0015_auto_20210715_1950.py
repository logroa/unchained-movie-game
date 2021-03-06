# Generated by Django 3.2.5 on 2021-07-16 00:50

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('movieweb', '0014_auto_20210715_1928'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='highscore',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='movieweb.scoreboard'),
        ),
        migrations.AlterField(
            model_name='scoreboard',
            name='date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2021, 7, 15, 19, 50, 50, 371457), null=True),
        ),
    ]

# Generated by Django 3.2.5 on 2021-07-20 22:01

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movieweb', '0015_auto_20210715_1950'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scoreboard',
            name='date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2021, 7, 20, 17, 1, 24, 125425), null=True),
        ),
    ]

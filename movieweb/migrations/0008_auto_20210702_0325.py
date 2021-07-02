# Generated by Django 3.2.4 on 2021-07-02 08:25

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movieweb', '0007_alter_scoreboard_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actor',
            name='name',
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='movie',
            name='title',
            field=models.CharField(max_length=200, unique=True),
        ),
        migrations.AlterField(
            model_name='scoreboard',
            name='date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2021, 7, 2, 3, 25, 46, 144004), null=True),
        ),
    ]

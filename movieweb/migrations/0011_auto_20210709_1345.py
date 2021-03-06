# Generated by Django 3.2.4 on 2021-07-09 18:45

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('movieweb', '0010_auto_20210706_1009'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('actsDisc', models.ManyToManyField(to='movieweb.Actor')),
                ('alwaysEndAct', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='playersEA', to='movieweb.turn')),
                ('alwaysEndMov', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='playersEM', to='movieweb.turn')),
                ('favAct', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='FplayersFA', to='movieweb.actor')),
                ('favMov', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='playersFM', to='movieweb.movie')),
                ('favRol', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='playersFR', to='movieweb.role')),
                ('favStart', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='playersFS', to='movieweb.turn')),
            ],
        ),
        migrations.AlterField(
            model_name='scoreboard',
            name='date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2021, 7, 9, 13, 45, 50, 288899), null=True),
        ),
        migrations.DeleteModel(
            name='playerRole',
        ),
        migrations.AddField(
            model_name='profile',
            name='highscore',
            field=models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, to='movieweb.scoreboard'),
        ),
        migrations.AddField(
            model_name='profile',
            name='movsDisc',
            field=models.ManyToManyField(to='movieweb.Movie'),
        ),
        migrations.AddField(
            model_name='profile',
            name='rolsDisc',
            field=models.ManyToManyField(to='movieweb.Role'),
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-20 19:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0008_person_is_organization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='person',
            name='end_year',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='person',
            name='start_year',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
    ]

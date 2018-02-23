# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-01-23 23:12
from __future__ import unicode_literals

from django.db import migrations

# set sex for people based unambiguously gendered titles
# list of titles here is based on a list generated from the database
# and annotated by the project team


FEMALE_TITLES = ['Miss', 'Mrs', 'Mlle', 'Mme', 'Mrs.', 'Miss.', 'Mme.',
    'Mlle.', 'Madame', 'Madame.', 'Comtesse', 'Ms', 'Lady', 'Baronne', 'Mme de',
    'Mademoiselle', 'Mlle de', 'Duchess de Clermont-Tonnerre',
    'Countess', 'Mlle des']

MALE_TITLES = ['Mr', 'Mr.', 'M.', 'M', 'M. de', 'Capt', 'M. Le',
    'Monsieur', 'Captain', 'Baron', 'Father', 'L\'Abbé', 'Sir', 'Vicomte',
    'Col/Mr', 'Colonel.', 'Marquis', 'Count', 'Major']


def infer_sex_from_title(apps, schema_editor):
    Person = apps.get_model("people", "Person")

    Person.objects.filter(sex='', title__in=FEMALE_TITLES)\
        .update(sex='F')
    Person.objects.filter(sex='', title__in=MALE_TITLES)\
        .update(sex='M')


class Migration(migrations.Migration):

    dependencies = [
        ('people', '0002_add_subtype_choices'),
    ]

    operations = [
        migrations.RunPython(infer_sex_from_title,
                             migrations.RunPython.noop)

    ]
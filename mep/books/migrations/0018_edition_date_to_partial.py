# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-03-12 14:02
from __future__ import unicode_literals
from datetime import date

from django.db import migrations

from mep.accounts.partial_date import DatePrecision


def edition_year_to_partial(apps, _schema_editor):
    '''
    Convert all year fields on Editions into partial dates with year precision.
    '''
    Edition = apps.get_model('books', 'Edition')
    # only convert editions with defined years
    for edition in Edition.objects.filter(year__isnull=False):
        # set precision to 'year' and store as datetime
        edition.date = date(edition.year, 1, 1)
        edition.date_precision = DatePrecision.year
        edition.save()


def edition_partial_to_year(apps, _schema_editor):
    '''
    Convert all partial dates on Editions into numeric year fields.
    '''
    Edition = apps.get_model('books', 'Edition')
    # only convert editions with defined dates
    for edition in Edition.objects.filter(date__isnull=False):
        # extract year and store it
        edition.year = edition.date.year
        edition.save()

class Migration(migrations.Migration):

    dependencies = [
        ('books', '0017_edition_details'),
    ]

    operations = [
        migrations.RunPython(edition_year_to_partial,
            reverse_code=edition_partial_to_year),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-01-25 17:18
from __future__ import unicode_literals

from django.db import migrations


def calculate_duration_in_days(apps, schema_editor):
    Subscription = apps.get_model("accounts", "Subscription")
    # recalculate duration in days as a timedelta between start and end date
    for subs in Subscription.objects.filter(start_date__isnull=False,
                                            end_date__isnull=False):
        subs.duration = (subs.end_date - subs.start_date).days
        subs.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_subscription_duration_to_days'),
    ]

    operations = [
            migrations.RunPython(calculate_duration_in_days,
                             migrations.RunPython.noop)
    ]

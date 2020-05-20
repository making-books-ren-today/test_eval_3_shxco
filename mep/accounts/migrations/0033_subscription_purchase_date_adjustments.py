# Generated by Django 2.2.11 on 2020-04-28 14:13

from dateutil.relativedelta import relativedelta
from django.db import migrations


def calculate_purchase_date(apps, schema_editor):
    '''populate purchase dates for subscription events'''
    Subscription = apps.get_model('accounts', 'Subscription')

    for sub in Subscription.objects.all():
        # in all cases, set purchase date from start date
        sub.purchase_date = sub.start_date
        # set precision to match also
        sub.purchase_date_precision = sub.start_date_precision

        # if this is a renewal with a start date, check if there is a
        # preceding subscription and recalculate subscription dates
        # - ignore supplements, since we expect them to overlap
        if sub.start_date and sub.subtype != 'sup':
            # find closest preceding subscription for the same account
            preceding_sub = Subscription.objects \
                .filter(account=sub.account,
                        start_date__lt=sub.start_date) \
                .exclude(pk=sub.pk) \
                .last()

            # if there is a preceding subscription with an end date
            if preceding_sub and preceding_sub.end_date:
                # next subscription should start the same day this one ends
                # (i.e., if may 1 - june 1, next is june 1 - july 1)
                next_start = preceding_sub.end_date
                # if current start is before expected next start, adjust
                if sub.start_date < next_start:
                    # if there is an end date, calculate relative duration
                    # and adjust before changing start date
                    if sub.end_date:
                        duration = relativedelta(sub.end_date, sub.start_date)
                        sub.end_date = next_start + duration

                    sub.start_date = next_start
        sub.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0032_subscription_add_purchase_date'),
    ]

    operations = [
        migrations.RunPython(
            code=calculate_purchase_date,
            reverse_code=migrations.RunPython.noop,
        ),
    ]

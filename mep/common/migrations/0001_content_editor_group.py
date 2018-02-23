# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-04 01:02
from __future__ import unicode_literals

from django.contrib.auth.management import create_permissions
from django.db import migrations


content_editor_perms = {
    'accounts': [
        'add_account', 'change_account', 'delete_account',
        'add_accountaddress', 'change_accountaddress', 'delete_accountaddress',
        'add_borrow', 'change_borrow', 'delete_borrow',
        'add_event', 'change_event', 'delete_event',
        'add_purchase', 'change_purchase', 'delete_purchase',
        'add_reimbursement', 'change_reimbursement', 'delete_reimbursement',
        'add_subscribe', 'change_subscribe', 'delete_subscribe'],
    'books': [
        'add_item', 'change_item', 'delete_item',
        'add_publisher', 'change_publisher', 'delete_publisher',
        'add_publisherplace', 'change_publisherplace', 'delete_publisherplace',
    ],
    "footnotes": [
        "add_bibliography", "change_bibliography", "delete_bibliography",
        "add_footnote", "change_footnote", "delete_footnote",
        "add_sourcetype", "change_sourcetype", "delete_sourcetype",
    ],
    "people": [
        "add_address", "change_address", "delete_address",
        "add_country", "change_country", "delete_country",
        "add_infourl", "change_infourl", "delete_infourl",
        "add_person", "change_person", "delete_person",
        "add_profession", "change_profession", "delete_profession",
        "add_relationship", "change_relationship", "delete_relationship",
        "add_relationshiptype", "change_relationshiptype", "delete_relationshiptype",
    ]
}



def create_content_editor_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # make sure permissions are created before loading the fixture
    # which references them
    # (when running migrations all at once, permissions may not yet exist)
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    editor_group, created = Group.objects.get_or_create(name='Content Editor')
    permissions = []
    for model, codenames in content_editor_perms.items():
        # using explicit get so that there will be an error if an
        # expected permission is not found
        for codename in codenames:
            try:
                permissions.append(Permission.objects.get(codename=codename))
            except Permission.DoesNotExist:
                # model rename means the permission codename can vary
                # depending on when this migration is run (old db or new setup)
                if 'subscribe' in codename:
                    codename = codename.replace('subscribe', 'subscription')
                    permissions.append(Permission.objects.get(codename=codename)
    )
    editor_group.permissions.set(permissions)


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        ('accounts', '0001_initial'),
        ('books', '0001_initial'),
        ('people', '0001_initial'),
        ('footnotes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_content_editor_group, reverse_code=migrations.RunPython.noop),
    ]


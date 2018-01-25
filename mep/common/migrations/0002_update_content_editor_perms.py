# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-01-25 16:47
from __future__ import unicode_literals

from django.contrib.auth.management import create_permissions
from django.db import migrations

new_content_editor_perms = {
    'accounts': [
        'add_subscription', 'change_subscription', 'delete_subscription',
        'add_subscriptiontype', 'change_subscriptiontype', 'delete_subscriptiontype',
        ],
}

remove_content_editor_perms = {
    'accounts': [
        'add_subscribe', 'change_subscribe', 'delete_subscribe',
    ]
}


def update_content_editor_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")

    # make sure permissions are created before loading the fixture
    # which references them
    # (when running migrations all at once, permissions may not yet exist)
    for app_config in apps.get_app_configs():
        app_config.models_module = True
        create_permissions(app_config, apps=apps, verbosity=0)
        app_config.models_module = None

    editor_group = Group.objects.get(name='Content Editor')
    permissions = []
    for model, codenames in new_content_editor_perms.items():
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
                    permissions.append(Permission.objects.get(codename=codename))

    # add the new permissions without removig existing ones
    editor_group.permissions.add(*permissions)

    # remove outdated permissions that are no longer needed (if present)
    for model, codenames in remove_content_editor_perms.items():
        editor_group.permissions.filter(codename__in=codenames).delete()




class Migration(migrations.Migration):

    dependencies = [
        ('common', '0001_content_editor_group'),
    ]

    operations = [
            migrations.RunPython(update_content_editor_group,
                reverse_code=migrations.RunPython.noop),
    ]

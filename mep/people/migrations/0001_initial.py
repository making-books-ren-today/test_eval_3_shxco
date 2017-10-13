# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-04 13:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import mep.common.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('street_address', models.CharField(blank=True, max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('postal_code', models.CharField(blank=True, max_length=25)),
                ('latitude', models.DecimalField(blank=True, decimal_places=5, max_digits=8, null=True, validators=[mep.common.validators.verify_latlon])),
                ('longitude', models.DecimalField(blank=True, decimal_places=5, max_digits=8, null=True, validators=[mep.common.validators.verify_latlon])),
            ],
            options={
                'verbose_name_plural': 'addresses',
            },
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('geonames_id', models.URLField(blank=True, help_text='GeoNames identifier', unique=True, verbose_name='GeoNames ID')),
                ('code', models.CharField(blank=True, help_text='Two-letter country code', max_length=2, unique=True, verbose_name='Country Code')),
            ],
            options={
                'verbose_name_plural': 'countries',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='InfoURL',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True)),
                ('url', models.URLField(help_text='Additional (non-VIAF) URLs for a person.')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True)),
                ('start_year', models.PositiveIntegerField(blank=True, null=True)),
                ('end_year', models.PositiveIntegerField(blank=True, null=True)),
                ('mep_id', models.CharField(blank=True, help_text='Identifier from XML personography', max_length=255, verbose_name='MEP id')),
                ('name', models.CharField(help_text='Name as firstname lastname, firstname (birthname) married name,\n        or psuedonym (real name)', max_length=255)),
                ('sort_name', models.CharField(help_text='Sort name in lastname, firstname format; VIAF authorized name if available', max_length=255)),
                ('viaf_id', models.URLField(blank=True, verbose_name='VIAF id')),
                ('sex', models.CharField(blank=True, choices=[('F', 'Female'), ('M', 'Male')], max_length=1)),
                ('title', models.CharField(blank=True, max_length=255)),
                ('addresses', models.ManyToManyField(blank=True, to='people.Address')),
                ('nationalities', models.ManyToManyField(blank=True, to='people.Country')),
            ],
            options={
                'verbose_name_plural': 'people',
                'ordering': ['sort_name'],
            },
        ),
        migrations.CreateModel(
            name='Profession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Relationship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.TextField(blank=True)),
                ('from_person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_relationships', to='people.Person')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RelationshipType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('notes', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['name'],
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='relationship',
            name='relationship_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='people.RelationshipType'),
        ),
        migrations.AddField(
            model_name='relationship',
            name='to_person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_relationships', to='people.Person'),
        ),
        migrations.AddField(
            model_name='person',
            name='profession',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='people.Profession'),
        ),
        migrations.AddField(
            model_name='person',
            name='relations',
            field=models.ManyToManyField(through='people.Relationship', to='people.Person'),
        ),
        migrations.AddField(
            model_name='infourl',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='urls', to='people.Person'),
        ),
        migrations.AddField(
            model_name='address',
            name='country',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='people.Country'),
        ),
    ]

# Generated by Django 2.2.11 on 2020-04-22 17:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('books', '0023_merge_20200406_1206'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='creator',
            options={'ordering': ['creator_type__order', 'order', 'person__sort_name']},
        ),
        migrations.AlterModelOptions(
            name='creatortype',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='work',
            name='sort_title',
            field=models.CharField(blank=True, help_text='Sort title autogenerated from title on record save.', max_length=255),
        ),
        migrations.AlterField(
            model_name='creatortype',
            name='order',
            field=models.PositiveSmallIntegerField(help_text='order in which creator types will be listed'),
        ),
        migrations.AlterField(
            model_name='work',
            name='slug',
            field=models.SlugField(blank=True, help_text='Short, durable, unique identifier for use in URLs. Save and continue editing to have a new slug autogenerated.Editing will change the public, citable URL for books.', max_length=255, null=True, unique=True),
        ),
        migrations.AlterModelOptions(
            name='work',
            options={'ordering': ['sort_title']},
        ),
    ]
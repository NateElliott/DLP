# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-30 18:32
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlp', '0022_modules_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='modules',
            name='published',
            field=models.BooleanField(default=False),
        ),
    ]

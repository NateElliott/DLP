# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-26 13:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlp', '0005_auto_20160926_1000'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitecode',
            name='used',
            field=models.BooleanField(default=False),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-26 14:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dlp', '0007_auto_20160926_1006'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('invite_limit', models.IntegerField()),
            ],
        ),
        migrations.AddField(
            model_name='invitecode',
            name='email',
            field=models.CharField(default='something', max_length=255, unique=True),
            preserve_default=False,
        ),
    ]

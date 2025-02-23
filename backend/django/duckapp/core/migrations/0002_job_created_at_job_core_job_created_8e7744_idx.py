# Generated by Django 5.1.5 on 2025-02-22 01:29

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddIndex(
            model_name="job",
            index=models.Index(
                fields=["created_at"], name="core_job_created_8e7744_idx"
            ),
        ),
    ]

# Generated by Django 3.2.14 on 2022-07-18 07:44

import django.db.models.deletion
from django.apps.registry import Apps
from django.db import migrations, models


def delete_django_celery_beat_data(apps: Apps, _schema_editor):
    """Wipe all exiting data from django-celery-beat in db.

    We need to do this otherwise we may get unique errors when trying to recreate
    the tasks using the new models.

    'PeriodicTasks' models doesn't need to be wiped as it doesn't have any relations.
    """
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.all().delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("django_celery_beat", "0016_alter_crontabschedule_timezone"),
    ]

    operations = [
        migrations.RunPython(delete_django_celery_beat_data, migrations.RunPython.noop),
        migrations.CreateModel(
            name="CustomSchedule",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "schedule_import_path",
                    models.CharField(
                        help_text=(
                            "The python import path where the Celery scheduler "
                            "is defined at"
                        ),
                        max_length=255,
                        unique=True,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CustomPeriodicTask",
            fields=[
                (
                    "periodictask_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="django_celery_beat.periodictask",
                    ),
                ),
                (
                    "custom",
                    models.ForeignKey(
                        blank=True,
                        help_text=(
                            "Custom Schedule to run the task on. Set only one "
                            "schedule type, leave the others null."
                        ),
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="schedulers.customschedule",
                        verbose_name="Custom Schedule",
                    ),
                ),
            ],
            bases=("django_celery_beat.periodictask",),
        ),
    ]

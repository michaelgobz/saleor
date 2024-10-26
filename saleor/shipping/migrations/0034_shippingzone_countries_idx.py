# Generated by Django 3.2.23 on 2024-04-24 12:23

import django.contrib.postgres.indexes
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("shipping", "0033_add_default_shipping"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="shippingzone",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["countries"],
                name="s_z_countries_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]

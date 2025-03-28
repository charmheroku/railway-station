# Generated by Django 5.1.6 on 2025-03-03 18:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("station", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Route",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "distance_km",
                    models.PositiveIntegerField(verbose_name="Distance (km)"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "destination_station",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="routes_to",
                        to="station.station",
                        verbose_name="Station of arrival",
                    ),
                ),
                (
                    "origin_station",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="routes_from",
                        to="station.station",
                        verbose_name="Station of departure",
                    ),
                ),
            ],
            options={
                "verbose_name": "Route",
                "verbose_name_plural": "Routes",
                "unique_together": {("origin_station", "destination_station")},
            },
        ),
    ]

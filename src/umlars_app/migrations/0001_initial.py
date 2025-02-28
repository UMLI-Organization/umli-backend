# Generated by Django 5.0.8 on 2024-08-27 18:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UmlModel",
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
                ("tech_valid_from", models.DateTimeField(auto_now_add=True)),
                ("tech_valid_to", models.DateTimeField(blank=True, null=True)),
                ("tech_active_flag", models.BooleanField(default=True)),
                ("name", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True, null=True)),
                ("formatted_data", models.TextField(blank=True, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="UmlFile",
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
                ("data", models.TextField()),
                (
                    "filename",
                    models.CharField(
                        blank=True, default=None, max_length=200, null=True
                    ),
                ),
                (
                    "format",
                    models.CharField(
                        choices=[
                            ("unknown", "Unknown"),
                            ("xmi_ea", "Enterprise Architect XMI"),
                            ("uml_papyrus", "Papyrus UML"),
                            ("notation_papyrus", "Papyrus Notation"),
                            ("mdj_staruml", "StarUML XMI"),
                        ],
                        default=None,
                        max_length=50,
                    ),
                ),
                (
                    "state",
                    models.IntegerField(
                        choices=[
                            (10, "Queued"),
                            (20, "Running"),
                            (30, "Finished"),
                            (40, "Partial Success"),
                            (50, "Failed"),
                        ],
                        default=10,
                    ),
                ),
                ("date_uploaded", models.DateTimeField(auto_now_add=True)),
                (
                    "model",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="source_files",
                        to="umlars_app.umlmodel",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="UserAccessToModel",
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
                    "access_level",
                    models.IntegerField(
                        choices=[(10, "Read"), (20, "Write")], default=20
                    ),
                ),
                (
                    "model",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="umlars_app.umlmodel",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="umlmodel",
            name="accessed_by",
            field=models.ManyToManyField(
                related_name="models",
                through="umlars_app.UserAccessToModel",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]

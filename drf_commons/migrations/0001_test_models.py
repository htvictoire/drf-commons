import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BaseModelForTesting",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Date and time when this record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Date and time when this record was last updated",
                    ),
                ),
                (
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Date and time when this record was soft deleted",
                        null=True,
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Indicates whether this record is active (not soft deleted)",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="User who created this record",
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="created_%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="User who last updated this record",
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="updated_%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SoftDeletableItem",
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
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Date and time when this record was soft deleted",
                        null=True,
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Indicates whether this record is active (not soft deleted)",
                    ),
                ),
                ("name", models.CharField(default="item", max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="SoftDeleteModelForTesting",
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
                    "deleted_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Date and time when this record was soft deleted",
                        null=True,
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Indicates whether this record is active (not soft deleted)",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="TimeStampModelForTesting",
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
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Date and time when this record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Date and time when this record was last updated",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="UserActionModelForTesting",
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
                ("name", models.CharField(max_length=100)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="User who created this record",
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="created_%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="User who last updated this record",
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="updated_%(class)s",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]

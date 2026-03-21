"""
Concrete models used only in the test suite.

These models exist to test library features that require concrete database
tables — e.g. bulk soft-delete, which needs deleted_at and is_active fields.
They are part of the drf_commons app so their tables are created automatically
by the test runner via the app's migrations.
"""

from django.db import models

from drf_commons.models.mixins import SoftDeleteMixin


class SoftDeletableItem(SoftDeleteMixin, models.Model):
    """
    Minimal concrete model for testing soft-delete functionality.

    Provides deleted_at and is_active from SoftDeleteMixin, plus a name
    field for factory use.
    """

    name = models.CharField(max_length=100, default="item")

    class Meta:
        app_label = "drf_commons"

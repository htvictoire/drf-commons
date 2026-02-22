"""
Base mixins for common model functionality.

This module contains fundamental mixins that provide core functionality
like user tracking, timestamps, and soft delete capabilities.
"""

import uuid

from django.db import models
from .mixins import JsonModelMixin, SoftDeleteMixin, TimeStampMixin, UserActionMixin


class BaseModelMixin(
        JsonModelMixin,
        UserActionMixin,
        TimeStampMixin,
        SoftDeleteMixin
    ):
    """
    Abstract base model that provides common functionality for all models.

    Combines UserActionMixin and TimeStampMixin with additional common features:
    - UUID primary key
    - Automatic user tracking
    - Timestamp tracking
    - JSON serialization method

    Attributes:
        id: UUID primary key
    """

    id = models.UUIDField(
        default=uuid.uuid4,
        primary_key=True,
        editable=False,
        help_text="Unique identifier for this record",
    )

    class Meta:
        abstract = True

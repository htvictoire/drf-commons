"""
Base mixins for common model functionality.

This module contains fundamental mixins that provide core functionality
like user tracking, timestamps, and soft delete capabilities.
"""

import json
import uuid
from typing import List, Optional, Set

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from .mixins import SoftDeleteMixin, TimeStampMixin, UserActionMixin


class BaseModelMixin(
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

    def get_json(
        self,
        exclude_fields: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
        exclude_general_fields: bool = False,
    ) -> str:
        """
        Return the JSON string representation of the model instance.

        Args:
            exclude_fields: List of field names to exclude from serialization
            fields: List of field names to include (if None, includes all)
            exclude_general_fields: Whether to exclude timestamp and user fields

        Returns:
            JSON string representation of the model instance
        """
        # Determine which fields to include
        if fields is not None:
            field_names = fields
        else:
            field_names = [f.name for f in self._meta.fields]

        # Apply exclusions
        if exclude_fields:
            field_names = [f for f in field_names if f not in exclude_fields]

        # Build data dictionary manually to ensure all fields are included
        data = {}
        for field_name in field_names:
            if hasattr(self, field_name):
                value = getattr(self, field_name)
                # Handle foreign key fields by getting their pk
                if hasattr(value, 'pk') and value is not None:
                    value = value.pk
                data[field_name] = value

        if exclude_general_fields:
            general_fields: Set[str] = {
                "created_at",
                "updated_at",
                "created_by",
                "updated_by",
            }
            data = {k: v for k, v in data.items() if k not in general_fields}

        return json.dumps(data, cls=DjangoJSONEncoder)

    class Meta:
        abstract = True

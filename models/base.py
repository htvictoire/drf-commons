"""
Base mixins for common model functionality.

This module contains fundamental mixins that provide core functionality
like user tracking, timestamps, and soft delete capabilities.
"""

import json
import uuid
from typing import List, Optional, Set

from django.conf import settings as django_settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.forms.models import model_to_dict
from django.utils import timezone

from ..current_user.utils import get_current_authenticated_user


class UserActionMixin(models.Model):
    """
    Mixin that automatically tracks which user created and last updated a model instance.
    
    Attributes:
        created_by: ForeignKey to the user who created this instance
        updated_by: ForeignKey to the user who last updated this instance
    """
    created_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        related_name='created_%(class)s',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who created this record"
    )
    updated_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        related_name='updated_%(class)s',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who last updated this record"
    )
    
    class Meta:
        abstract = True


class TimeStampMixin(models.Model):
    """
    Mixin that automatically adds creation and modification timestamps.
    
    Attributes:
        created_at: DateTime when the instance was created
        updated_at: DateTime when the instance was last updated
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when this record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Date and time when this record was last updated"
    )
    
    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Mixin that provides soft delete functionality.
    
    Instead of permanently deleting records from the database, this mixin
    marks them as deleted by setting the deleted_at timestamp.
    
    Attributes:
        deleted_at: DateTime when the record was soft deleted (None if not deleted)
        is_deleted: Property to check if the record is soft deleted
    """
    
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when this record was soft deleted"
    )
    
    class Meta:
        abstract = True
    
    def soft_delete(self) -> None:
        """
        Soft delete this instance by setting deleted_at to current timestamp.
        """
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])
    
    def restore(self) -> None:
        """
        Restore a soft deleted instance by clearing the deleted_at field.
        """
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])
    
    @property
    def is_deleted(self) -> bool:
        """
        Check if this instance is soft deleted.
        
        Returns:
            True if the instance is soft deleted, False otherwise
        """
        return self.deleted_at is not None


class AbstractBaseModel(UserActionMixin, TimeStampMixin):
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
        help_text="Unique identifier for this record"
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        get_latest_by = "-created_at"

    def save(self, *args, **kwargs) -> None:
        """
        Override save method to automatically set created_by and updated_by fields.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        self.set_created_by_and_updated_by()
        return super().save(*args, **kwargs)

    def set_created_by_and_updated_by(self) -> None:
        """
        Automatically set created_by and updated_by fields based on current authenticated user.
        
        Sets created_by only if it's not already set (for new instances).
        Always updates updated_by with current user.
        """
        current_user = get_current_authenticated_user()
        if current_user and current_user.is_authenticated:
            if not self.created_by:
                self.created_by = current_user
            self.updated_by = current_user

    def get_json(
        self,
        exclude_fields: Optional[List[str]] = None,
        fields: Optional[List[str]] = None,
        exclude_general_fields: bool = False
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
        data = model_to_dict(self, fields=fields, exclude=exclude_fields)
        
        if exclude_general_fields:
            general_fields: Set[str] = {"created_at", "updated_at", "created_by", "updated_by"}
            data = {k: v for k, v in data.items() if k not in general_fields}
        
        return json.dumps(data, cls=DjangoJSONEncoder)
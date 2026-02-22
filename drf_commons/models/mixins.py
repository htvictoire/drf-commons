import json
from typing import List, Optional, Set, Union

from django.conf import settings as django_settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone

from drf_commons.current_user.utils import get_current_authenticated_user


class UserActionMixin(models.Model):
    """
    Mixin that automatically tracks which user created and last updated a model instance.

    Attributes:
        created_by: ForeignKey to the user who created this instance
        updated_by: ForeignKey to the user who last updated this instance
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    created_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        related_name="created_%(class)s",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who created this record",
    )
    updated_by = models.ForeignKey(
        django_settings.AUTH_USER_MODEL,
        related_name="updated_%(class)s",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who last updated this record",
    )

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
        if current_user:
            if not self.created_by:
                self.created_by = current_user
            self.updated_by = current_user

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
        auto_now_add=True, help_text="Date and time when this record was created"
    )
    updated_at = models.DateTimeField(
        auto_now=True, help_text="Date and time when this record was last updated"
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
        help_text="Date and time when this record was soft deleted",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Indicates whether this record is active (not soft deleted)",
    )

    def soft_delete(self) -> None:
        """
        Soft delete this instance by setting deleted_at to current timestamp.
        """
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save()

    def restore(self) -> None:
        """
        Restore a soft deleted instance by clearing the deleted_at field.
        """
        self.deleted_at = None
        self.is_active = True
        self.save()

    @property
    def is_deleted(self) -> bool:
        """
        Check if this instance is soft deleted.

        Returns:
            True if the instance is soft deleted, False otherwise
        """
        return not self.is_active

    class Meta:
        abstract = True


class JsonModelMixin(models.Model):
    """Mixin that provides JSON serialization for model instances."""

    def get_json(
        self,
        exclude_fields: Optional[List[str]] = None,
        fields: Optional[Union[List[str], str]] = None,
        exclude_general_fields: bool = False,
    ) -> str:
        """
        Return the JSON string representation of the model instance.

        Args:
            exclude_fields: List of field names to exclude from serialization
            fields: List of field names to include, or "__all__"
            exclude_general_fields: Whether to exclude timestamp and user fields

        Returns:
            JSON string representation of the model instance
        """
        if fields is None and exclude_fields is None:
            raise ValueError(
                "Either 'fields' or 'exclude_fields' must be provided."
            )

        if fields == "__all__":
            field_names = [f.name for f in self._meta.fields]
        elif fields is not None:
            if isinstance(fields, str):
                raise ValueError(
                    "Invalid 'fields' value. Use a list of field names or '__all__'."
                )
            field_names = fields
        else:
            field_names = [f.name for f in self._meta.fields]

        if exclude_fields:
            field_names = [f for f in field_names if f not in exclude_fields]

        data = {}
        for field_name in field_names:
            if hasattr(self, field_name):
                value = getattr(self, field_name)
                if value is not None and hasattr(value, "pk"):
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

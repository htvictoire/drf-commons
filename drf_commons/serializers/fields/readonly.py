"""
Read-only related field types for common use cases.

This module provides pre-configured read-only field types
to avoid repetitive configuration and ensure consistency.
"""

from typing import Any, Callable

from .base import ReadOnlyRelatedField


class ReadOnlyIdField(ReadOnlyRelatedField):
    """
    Read-only field that returns only the ID of related object.

    Example:
        created_by_id = ReadOnlyIdField()
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("output_format", "id")
        super().__init__(**kwargs)


class ReadOnlyStrField(ReadOnlyRelatedField):
    """
    Read-only field that returns string representation of related object.

    Example:
        created_by_name = ReadOnlyStrField()
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("output_format", "str")
        super().__init__(**kwargs)


class ReadOnlyDataField(ReadOnlyRelatedField):
    """
    Read-only field that returns full serialized data of related object.

    Example:
        created_by = ReadOnlyDataField(serializer_class=UserSerializer)
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class ReadOnlyCustomField(ReadOnlyRelatedField):
    """
    Read-only field with custom output formatting.

    Example:
        created_by_display = ReadOnlyCustomField(
            custom_output_callable=lambda user, ctx: f"{user.first_name} {user.last_name}"
        )
    """

    def __init__(self, custom_output_callable: Callable[[Any, dict], Any], **kwargs):
        kwargs["custom_output_callable"] = custom_output_callable
        kwargs.setdefault("output_format", "custom")
        super().__init__(**kwargs)

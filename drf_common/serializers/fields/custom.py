"""
Custom and flexible related field types for advanced use cases.

This module provides configurable field types that offer maximum flexibility
for complex serialization scenarios.
"""

from typing import Any, Callable

from .base import ConfigurableRelatedField


class FlexibleField(ConfigurableRelatedField):
    """
    Field that accepts multiple input formats and returns serialized data.

    Input: ID, nested data, or string lookup
    Output: Full serialized object

    Example:
        author = FlexibleField(
            queryset=Author.objects.all(),
            serializer_class=AuthorSerializer
        )
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["id", "nested", "slug"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class CustomOutputField(ConfigurableRelatedField):
    """
    Field with custom output formatting function.

    Input: ID or nested data
    Output: Custom format via callable

    Example:
        author = CustomOutputField(
            queryset=Author.objects.all(),
            serializer_class=AuthorSerializer,
            custom_output_callable=lambda obj, ctx: f"{obj.name} <{obj.email}>"
        )
    """

    def __init__(self, custom_output_callable: Callable[[Any, dict], Any], **kwargs):
        kwargs["custom_output_callable"] = custom_output_callable
        kwargs.setdefault("input_formats", ["id", "nested"])
        kwargs.setdefault("output_format", "custom")
        super().__init__(**kwargs)

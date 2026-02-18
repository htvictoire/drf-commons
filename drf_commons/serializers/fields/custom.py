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

    relation_write:
        Optional dict forwarded to relation-write resolution.
        Keys: ``relation_kind``, ``write_order``, ``child_link_field``, ``sync_mode``.
        If omitted, inferred relation metadata and default sync behavior are used.

    Example:
        author = FlexibleField(
            queryset=Author.objects.all(),
            serializer_class=AuthorSerializer
        )
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["id", "nested", "slug"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class CustomOutputField(ConfigurableRelatedField):
    """
    Field with custom output formatting function.

    Input: ID or nested data
    Output: Custom format via callable

    relation_write:
        Optional dict for relation write orchestration overrides.
        This only affects write-time relation behavior; output remains controlled by
        ``custom_output_callable``.

    Example:
        author = CustomOutputField(
            queryset=Author.objects.all(),
            serializer_class=AuthorSerializer,
            custom_output_callable=lambda obj, ctx: f"{obj.name} <{obj.email}>"
        )
    """

    def __init__(
        self,
        custom_output_callable: Callable[[Any, dict], Any],
        relation_write=None,
        **kwargs,
    ):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs["custom_output_callable"] = custom_output_callable
        kwargs.setdefault("input_formats", ["id", "nested"])
        kwargs.setdefault("output_format", "custom")
        super().__init__(**kwargs)

"""
Many-to-many related field types for common use cases.

This module provides pre-configured many-to-many field types
to avoid repetitive configuration and ensure consistency.
"""

from .base import ConfigurableManyToManyField


class ManyIdToDataField(ConfigurableManyToManyField):
    """
    Many-to-many field that accepts list of IDs and returns list of serialized data.

    Input: [1, 2, 3]
    Output: [{"id": 1, "name": "..."}, {"id": 2, "name": "..."}, ...]

    relation_write:
        Optional dict forwarded to relation-write resolution in the mixin.
        Supported keys:
        - ``relation_kind``: ``auto|generic|fk|m2m|reverse_fk|reverse_m2m``
        - ``write_order``: ``auto|dependency_first|root_first``
        - ``child_link_field``: reverse FK child link (required when not inferable)
        - ``sync_mode``: ``append|replace|sync``

    Example:
        tags = ManyIdToDataField(
            queryset=Tag.objects.all(),
            serializer_class=TagSerializer
        )
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["id"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class ManyDataToIdField(ConfigurableManyToManyField):
    """
    Many-to-many field that accepts list of nested data and returns list of IDs.

    Input: [{"name": "tag1"}, {"name": "tag2"}]
    Output: [1, 2]

    relation_write:
        Optional dict controlling when nested children are persisted and how links
        are applied on root-first relation managers.
        Nested rows are validated during ``is_valid()`` and persisted during parent
        serializer ``save()``.

    Example:
        tag_ids = ManyDataToIdField(
            queryset=Tag.objects.all(),
            serializer_class=TagSerializer
        )
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["nested", "id"])
        kwargs.setdefault("output_format", "id")
        super().__init__(**kwargs)


class ManyStrToDataField(ConfigurableManyToManyField):
    """
    Many-to-many field that accepts list of strings and returns list of serialized data.

    Input: ["tag1", "tag2", "tag3"]
    Output: [{"id": 1, "name": "tag1"}, {"id": 2, "name": "tag2"}, ...]

    relation_write:
        Optional dict for relation-write override; auto inference is used when
        omitted.

    Example:
        tags = ManyStrToDataField(
            queryset=Tag.objects.all(),
            serializer_class=TagSerializer
        )
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["slug"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class ManyIdOnlyField(ConfigurableManyToManyField):
    """
    Many-to-many field that accepts and returns only lists of IDs.

    Input: [1, 2, 3]
    Output: [1, 2, 3]

    relation_write:
        Optional dict for relation write orchestration override.

    Example:
        tag_ids = ManyIdOnlyField(queryset=Tag.objects.all())
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["id"])
        kwargs.setdefault("output_format", "id")
        super().__init__(**kwargs)


class ManyStrOnlyField(ConfigurableManyToManyField):
    """
    Many-to-many field that accepts and returns only lists of strings.

    Input: ["tag1", "tag2"]
    Output: ["tag1", "tag2"]

    relation_write:
        Optional dict for relation write orchestration override.

    Example:
        tag_names = ManyStrOnlyField(queryset=Tag.objects.all())
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["slug"])
        kwargs.setdefault("output_format", "str")
        super().__init__(**kwargs)


class ManyFlexibleField(ConfigurableManyToManyField):
    """
    Many-to-many field that accepts multiple input formats and returns serialized data.

    Input: Mix of IDs, nested data, and strings
    Output: List of serialized objects

    relation_write:
        Optional dict for explicit relation orchestration.
        For reverse FK use-cases routed through this field, set
        ``child_link_field`` when inference is not reliable.

    Example:
        tags = ManyFlexibleField(
            queryset=Tag.objects.all(),
            serializer_class=TagSerializer
        )
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["id", "nested", "slug"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)

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

    Example:
        tags = ManyIdToDataField(
            queryset=Tag.objects.all(),
            serializer_class=TagSerializer
        )
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["id"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class ManyDataToIdField(ConfigurableManyToManyField):
    """
    Many-to-many field that accepts list of nested data and returns list of IDs.

    Input: [{"name": "tag1"}, {"name": "tag2"}]
    Output: [1, 2]

    Example:
        tag_ids = ManyDataToIdField(
            queryset=Tag.objects.all(),
            serializer_class=TagSerializer
        )
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["nested", "id"])
        kwargs.setdefault("output_format", "id")
        super().__init__(**kwargs)


class ManyStrToDataField(ConfigurableManyToManyField):
    """
    Many-to-many field that accepts list of strings and returns list of serialized data.

    Input: ["tag1", "tag2", "tag3"]
    Output: [{"id": 1, "name": "tag1"}, {"id": 2, "name": "tag2"}, ...]

    Example:
        tags = ManyStrToDataField(
            queryset=Tag.objects.all(),
            serializer_class=TagSerializer
        )
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["slug"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class ManyIdOnlyField(ConfigurableManyToManyField):
    """
    Many-to-many field that accepts and returns only lists of IDs.

    Input: [1, 2, 3]
    Output: [1, 2, 3]

    Example:
        tag_ids = ManyIdOnlyField(queryset=Tag.objects.all())
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["id"])
        kwargs.setdefault("output_format", "id")
        super().__init__(**kwargs)


class ManyStrOnlyField(ConfigurableManyToManyField):
    """
    Many-to-many field that accepts and returns only lists of strings.

    Input: ["tag1", "tag2"]
    Output: ["tag1", "tag2"]

    Example:
        tag_names = ManyStrOnlyField(queryset=Tag.objects.all())
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["slug"])
        kwargs.setdefault("output_format", "str")
        super().__init__(**kwargs)


class ManyFlexibleField(ConfigurableManyToManyField):
    """
    Many-to-many field that accepts multiple input formats and returns serialized data.

    Input: Mix of IDs, nested data, and strings
    Output: List of serialized objects

    Example:
        tags = ManyFlexibleField(
            queryset=Tag.objects.all(),
            serializer_class=TagSerializer
        )
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["id", "nested", "slug"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)

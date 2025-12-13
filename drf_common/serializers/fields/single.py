"""
Single related field types for common use cases.

This module provides pre-configured single related field types
to avoid repetitive configuration and ensure consistency.
"""

from .base import ConfigurableRelatedField


class IdToDataField(ConfigurableRelatedField):
    """
    Field that accepts ID input and returns full serialized data.

    Input: Integer/String ID
    Output: Full serialized object

    Example:
        author = IdToDataField(
            queryset=Author.objects.all(),
            serializer_class=AuthorSerializer
        )
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["id"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class IdToStrField(ConfigurableRelatedField):
    """
    Field that accepts ID input and returns string representation.

    Input: Integer/String ID
    Output: String representation of the object (__str__)

    Example:
        author = IdToStrField(
            queryset=Author.objects.all()
        )
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["id"])
        kwargs.setdefault("output_format", "str")
        super().__init__(**kwargs)


class DataToIdField(ConfigurableRelatedField):
    """
    Field that accepts nested data input and returns only ID.

    Input: Nested dictionary (creates/updates object)
    Output: Object ID

    Example:
        author = DataToIdField(
            queryset=Author.objects.all(),
            serializer_class=AuthorSerializer
        )
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["nested", "id"])
        kwargs.setdefault("output_format", "id")
        super().__init__(**kwargs)


class DataToDataField(ConfigurableRelatedField):
    """
    Field that accepts nested data input and returns the entire object.

    Input: Nested dictionary (creates/updates object)
    Output: Full serialized object

    Example:
        author = DataToDataField(
            queryset=Author.objects.all(),
            serializer_class=AuthorSerializer
        )
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["nested"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class DataToStrField(ConfigurableRelatedField):
    """
    Field that accepts nested data input and returns string representation.

    Input: Nested dictionary (creates/updates object)
    Output: String representation of object

    Example:
        category = DataToStrField(
            queryset=Category.objects.all(),
            serializer_class=CategorySerializer
        )
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["nested", "id"])
        kwargs.setdefault("output_format", "str")
        super().__init__(**kwargs)


class StrToDataField(ConfigurableRelatedField):
    """
    Field that accepts string input (slug/name lookup) and returns full data.

    Input: String (looks up by slug or name field)
    Output: Full serialized object

    Example:
        category = StrToDataField(
            queryset=Category.objects.all(),
            serializer_class=CategorySerializer
        )
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["slug"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class IdOnlyField(ConfigurableRelatedField):
    """
    Field that accepts and returns only IDs.

    Input: Integer/String ID
    Output: Integer/String ID

    Example:
        author_id = IdOnlyField(queryset=Author.objects.all())
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["id"])
        kwargs.setdefault("output_format", "id")
        super().__init__(**kwargs)


class StrOnlyField(ConfigurableRelatedField):
    """
    Field that accepts and returns only string representations.

    Input: String (slug/name lookup)
    Output: String representation

    Example:
        category_name = StrOnlyField(queryset=Category.objects.all())
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("input_formats", ["slug"])
        kwargs.setdefault("output_format", "str")
        super().__init__(**kwargs)

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

    relation_write:
        Optional dict forwarded unchanged to ``ConfigurableRelatedFieldMixin``.
        Supported keys:
        - ``relation_kind``: ``auto|generic|fk|m2m|reverse_fk|reverse_m2m``
        - ``write_order``: ``auto|dependency_first|root_first``
        - ``child_link_field``: required for reverse FK linking when not inferable
        - ``sync_mode``: ``append|replace|sync``
        Defaults when omitted are auto relation/write-order and append sync.

    Example:
        author = IdToDataField(
            queryset=Author.objects.all(),
            serializer_class=AuthorSerializer
        )
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["id"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class IdToStrField(ConfigurableRelatedField):
    """
    Field that accepts ID input and returns string representation.

    Input: Integer/String ID
    Output: String representation of the object (__str__)

    relation_write:
        Optional relation orchestration override for save-time behavior.
        If omitted, relation metadata inference is used.

    Example:
        author = IdToStrField(
            queryset=Author.objects.all()
        )
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["id"])
        kwargs.setdefault("output_format", "str")
        super().__init__(**kwargs)


class DataToIdField(ConfigurableRelatedField):
    """
    Field that accepts nested data input and returns only ID.

    Input: Nested dictionary (validated immediately; persisted at serializer save)
    Output: Object ID

    relation_write:
        Optional dict controlling nested relation persistence ordering.
        Use explicit ``relation_write`` when field source maps to reverse relations
        or when you need non-default sync behavior.

    Example:
        author = DataToIdField(
            queryset=Author.objects.all(),
            serializer_class=AuthorSerializer
        )
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["nested", "id"])
        kwargs.setdefault("output_format", "id")
        super().__init__(**kwargs)


class DataToDataField(ConfigurableRelatedField):
    """
    Field that accepts nested data input and returns the entire object.

    Input: Nested dictionary (validated immediately; persisted at serializer save)
    Output: Full serialized object

    relation_write:
        Optional dict forwarded unchanged to relation-write resolution.
        Reverse FK paths may require explicit ``child_link_field``.

    Example:
        author = DataToDataField(
            queryset=Author.objects.all(),
            serializer_class=AuthorSerializer
        )
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["nested"])
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class DataToStrField(ConfigurableRelatedField):
    """
    Field that accepts nested data input and returns string representation.

    Input: Nested dictionary (validated immediately; persisted at serializer save)
    Output: String representation of object

    relation_write:
        Optional dict for relation orchestration.
        Use explicit config for reverse relation manager writes.

    Example:
        category = DataToStrField(
            queryset=Category.objects.all(),
            serializer_class=CategorySerializer
        )
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["nested", "id"])
        kwargs.setdefault("output_format", "str")
        super().__init__(**kwargs)


class StrToDataField(ConfigurableRelatedField):
    """
    Field that accepts string input (slug/name lookup) and returns full data.

    Input: String (looks up by slug or name field)
    Output: Full serialized object

    relation_write:
        Optional dict for overriding inferred relation write behavior.

    Example:
        category = StrToDataField(
            queryset=Category.objects.all(),
            serializer_class=CategorySerializer
        )
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["slug"])
        kwargs.setdefault("slug_lookup_field", "slug")
        kwargs.setdefault("output_format", "serialized")
        super().__init__(**kwargs)


class IdOnlyField(ConfigurableRelatedField):
    """
    Field that accepts and returns only IDs.

    Input: Integer/String ID
    Output: Integer/String ID

    relation_write:
        Optional dict for relation write orchestration overrides.

    Example:
        author_id = IdOnlyField(queryset=Author.objects.all())
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["id"])
        kwargs.setdefault("output_format", "id")
        super().__init__(**kwargs)


class StrOnlyField(ConfigurableRelatedField):
    """
    Field that accepts and returns only string representations.

    Input: String (slug/name lookup)
    Output: String representation

    relation_write:
        Optional dict for relation write orchestration overrides.

    Example:
        category_name = StrOnlyField(queryset=Category.objects.all())
    """

    def __init__(self, relation_write=None, **kwargs):
        if relation_write is not None:
            kwargs.setdefault("relation_write", relation_write)
        kwargs.setdefault("input_formats", ["slug"])
        kwargs.setdefault("slug_lookup_field", "slug")
        kwargs.setdefault("output_format", "str")
        super().__init__(**kwargs)

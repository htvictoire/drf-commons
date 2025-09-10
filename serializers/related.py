"""
Common related field types for serializers.

This module provides pre-configured field types for common use cases
to avoid repetitive configuration and ensure consistency.
"""

from typing import Any, Callable

from .core import ConfigurableRelatedField, ConfigurableManyToManyField, ReadOnlyRelatedField


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
        kwargs.setdefault('input_formats', ['id'])
        kwargs.setdefault('output_format', 'serialized')
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
        kwargs.setdefault('input_formats', ['id'])
        kwargs.setdefault('output_format', 'str')
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
        kwargs.setdefault('input_formats', ['nested', 'id'])
        kwargs.setdefault('output_format', 'id')
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
        kwargs.setdefault('input_formats', ['nested'])
        kwargs.setdefault('output_format', 'serialized')
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
        kwargs.setdefault('input_formats', ['nested', 'id'])
        kwargs.setdefault('output_format', 'str')
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
        kwargs.setdefault('input_formats', ['slug'])
        kwargs.setdefault('output_format', 'serialized')
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
        kwargs.setdefault('input_formats', ['id'])
        kwargs.setdefault('output_format', 'id')
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
        kwargs.setdefault('input_formats', ['slug'])
        kwargs.setdefault('output_format', 'str')
        super().__init__(**kwargs)


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
        kwargs.setdefault('input_formats', ['id', 'nested', 'slug'])
        kwargs.setdefault('output_format', 'serialized')
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
        kwargs['custom_output_callable'] = custom_output_callable
        kwargs.setdefault('input_formats', ['id', 'nested'])
        kwargs.setdefault('output_format', 'custom')
        super().__init__(**kwargs)


# Many-to-Many Field Types

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
        kwargs.setdefault('input_formats', ['id'])
        kwargs.setdefault('output_format', 'serialized')
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
        kwargs.setdefault('input_formats', ['nested', 'id'])
        kwargs.setdefault('output_format', 'id')
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
        kwargs.setdefault('input_formats', ['slug'])
        kwargs.setdefault('output_format', 'serialized')
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
        kwargs.setdefault('input_formats', ['id'])
        kwargs.setdefault('output_format', 'id')
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
        kwargs.setdefault('input_formats', ['slug'])
        kwargs.setdefault('output_format', 'str')
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
        kwargs.setdefault('input_formats', ['id', 'nested', 'slug'])
        kwargs.setdefault('output_format', 'serialized')
        super().__init__(**kwargs)


# Read-Only Field Types

class ReadOnlyIdField(ReadOnlyRelatedField):
    """
    Read-only field that returns only the ID of related object.
    
    Example:
        created_by_id = ReadOnlyIdField()
    """
    
    def __init__(self, **kwargs):
        kwargs.setdefault('output_format', 'id')
        super().__init__(**kwargs)


class ReadOnlyStrField(ReadOnlyRelatedField):
    """
    Read-only field that returns string representation of related object.
    
    Example:
        created_by_name = ReadOnlyStrField()
    """
    
    def __init__(self, **kwargs):
        kwargs.setdefault('output_format', 'str')
        super().__init__(**kwargs)


class ReadOnlyDataField(ReadOnlyRelatedField):
    """
    Read-only field that returns full serialized data of related object.
    
    Example:
        created_by = ReadOnlyDataField(serializer_class=UserSerializer)
    """
    
    def __init__(self, **kwargs):
        kwargs.setdefault('output_format', 'serialized')
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
        kwargs['custom_output_callable'] = custom_output_callable
        kwargs.setdefault('output_format', 'custom')
        super().__init__(**kwargs)
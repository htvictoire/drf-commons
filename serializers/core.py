"""
Core configurable field implementations.

This module contains the main configurable field classes that use
the mixins to provide flexible related field functionality.
"""

from rest_framework import serializers
from .mixins import ConfigurableRelatedFieldMixin


class ConfigurableRelatedField(ConfigurableRelatedFieldMixin, serializers.RelatedField):
    """
    A configurable related field for ForeignKey and OneToOneField relationships.
    
    Examples:
        # Basic usage - accepts ID or nested dict, returns serialized
        author = ConfigurableRelatedField(
            queryset=Author.objects.all(),
            serializer_class=AuthorSerializer
        )
        
        # Returns only ID
        author = ConfigurableRelatedField(
            queryset=Author.objects.all(),
            output_format='id'
        )
        
        # Returns string representation
        category = ConfigurableRelatedField(
            queryset=Category.objects.all(),
            output_format='str'
        )
        
        # Custom output format
        author = ConfigurableRelatedField(
            queryset=Author.objects.all(),
            output_format='custom',
            custom_output_callable=lambda obj, ctx: f"{obj.name} ({obj.email})"
        )
    """
    pass


class ConfigurableManyToManyField(ConfigurableRelatedFieldMixin, serializers.RelatedField):
    """
    A configurable many-to-many related field.
    
    Examples:
        # Accepts list of IDs or list of nested dicts
        tags = ConfigurableManyToManyField(
            queryset=Tag.objects.all(),
            serializer_class=TagSerializer,
            many=True
        )
        
        # Returns only IDs
        tag_ids = ConfigurableManyToManyField(
            queryset=Tag.objects.all(),
            output_format='id',
            many=True
        )
    """
    
    def __init__(self, **kwargs):
        kwargs['many'] = True
        super().__init__(**kwargs)

    def to_representation(self, value):
        """Handle many=True representation."""
        if not value:
            return []
        
        return [super(ConfigurableManyToManyField, self).to_representation(item) 
                for item in value.all()]

    def to_internal_value(self, data):
        """Handle many=True internal value conversion."""
        if not isinstance(data, list):
            raise serializers.ValidationError("Expected a list of items.")
        
        if not data:
            return []
        
        return [super(ConfigurableManyToManyField, self).to_internal_value(item) 
                for item in data]


class ReadOnlyRelatedField(ConfigurableRelatedFieldMixin, serializers.RelatedField):
    """
    A read-only related field that can format output in various ways.
    
    Examples:
        # Show related object as string
        created_by = ReadOnlyRelatedField(output_format='str')
        
        # Show full serialized related object
        department = ReadOnlyRelatedField(
            serializer_class=DepartmentSerializer,
            output_format='serialized'
        )
    """
    
    def __init__(self, **kwargs):
        kwargs['read_only'] = True
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        """Read-only field should not accept input."""
        raise serializers.ValidationError("This field is read-only.")


class WriteOnlyRelatedField(ConfigurableRelatedFieldMixin, serializers.RelatedField):
    """
    A write-only related field for input processing without output.
    
    Examples:
        # Accept nested data for creation but don't include in output
        author_data = WriteOnlyRelatedField(
            queryset=Author.objects.all(),
            serializer_class=AuthorSerializer,
            create_if_nested=True
        )
    """
    
    def __init__(self, **kwargs):
        kwargs['write_only'] = True
        super().__init__(**kwargs)

    def to_representation(self, value):
        """Write-only field should not provide output."""
        return None
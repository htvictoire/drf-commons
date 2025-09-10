"""
Reusable mixins for configurable related fields.

This module contains the core mixins that provide the foundation
for all configurable related field functionality.
"""

from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers


class ConfigurableRelatedFieldMixin:
    """
    Base mixin providing core functionality for configurable related fields.
    """
    
    def __init__(self, 
                 serializer_class=None,
                 input_formats=None,
                 output_format='serialized',
                 lookup_field='pk',
                 create_if_nested=True,
                 update_if_exists=False,
                 custom_output_callable=None,
                 **kwargs):
        """
        Initialize the configurable related field.
        
        Args:
            serializer_class: Serializer class for nested operations
            input_formats: List of accepted input formats ['id', 'nested', 'slug', 'object']
            output_format: Output format - 'id', 'str', 'serialized', 'custom'
            lookup_field: Field to use for lookups (default: 'pk')
            create_if_nested: Whether to create objects from nested data
            update_if_exists: Whether to update existing objects with nested data
            custom_output_callable: Custom function for output formatting
        """
        # Store our custom configuration
        self.serializer_class = serializer_class
        self.input_formats = input_formats or ['id', 'nested']
        self.output_format = output_format
        self.lookup_field = lookup_field
        self.create_if_nested = create_if_nested
        self.update_if_exists = update_if_exists
        self.custom_output_callable = custom_output_callable
        
        # Let DRF handle its own parameters (allow_null, required, etc.)
        super().__init__(**kwargs)
        
        # Validate our custom configuration
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate field configuration."""
        valid_input_formats = ['id', 'nested', 'slug', 'object']
        valid_output_formats = ['id', 'str', 'serialized', 'custom']
        
        if not all(fmt in valid_input_formats for fmt in self.input_formats):
            raise ValueError(f"Invalid input_formats. Must be subset of {valid_input_formats}")
        
        if self.output_format not in valid_output_formats:
            raise ValueError(f"Invalid output_format. Must be one of {valid_output_formats}")
        
        if self.output_format == 'serialized' and not self.serializer_class:
            raise ValueError("serializer_class is required when output_format='serialized'")
        
        if self.output_format == 'custom' and not self.custom_output_callable:
            raise ValueError("custom_output_callable is required when output_format='custom'")
        
        if 'nested' in self.input_formats and not self.serializer_class:
            raise ValueError("serializer_class is required when 'nested' is in input_formats")

    def to_representation(self, value):
        """Convert the internal value to the desired output format."""
        if value is None:
            return None
        
        if self.output_format == 'id':
            return getattr(value, self.lookup_field)
        
        elif self.output_format == 'str':
            return str(value)
        
        elif self.output_format == 'serialized':
            serializer = self.serializer_class(value, context=self.context)
            return serializer.data
        
        elif self.output_format == 'custom':
            return self.custom_output_callable(value, self.context)
        
        else:
            # Fallback to serialized or string representation
            if self.serializer_class:
                serializer = self.serializer_class(value, context=self.context)
                return serializer.data
            return str(value)

    def to_internal_value(self, data):
        """Convert input data to internal value."""
        # Let DRF handle null validation first by calling parent's validation
        # This ensures DRF's allow_null, required, and empty string handling works properly
        
        # Handle null/None/empty string values using DRF's built-in logic
        if data is None or data == '':
            if not self.allow_null:
                self.fail('null')
            return None
        
        # Now handle our custom input formats
        # Handle nested dictionary input
        if isinstance(data, dict) and 'nested' in self.input_formats:
            return self._handle_nested_input(data)
        
        # Handle ID input (integer or string)
        if isinstance(data, (int, str)) and 'id' in self.input_formats:
            return self._handle_id_input(data)
        
        # Handle object input (already an instance)
        if hasattr(data, '_meta') and 'object' in self.input_formats:
            return data
        
        # Handle slug input (string lookup)
        if isinstance(data, str) and 'slug' in self.input_formats:
            return self._handle_slug_input(data)
        
        self.fail('incorrect_type', data_type=type(data).__name__)

    def _handle_nested_input(self, data):
        """Handle nested dictionary input for create/update operations."""
        if not self.create_if_nested:
            self.fail('invalid')
        
        # Check if this is an update operation (has ID in nested data)
        lookup_value = data.get(self.lookup_field)
        
        if lookup_value and self.update_if_exists:
            return self._handle_nested_update(data, lookup_value)
        else:
            return self._handle_nested_create(data)

    def _handle_nested_create(self, data):
        """Create a new object from nested data."""
        serializer = self.serializer_class(data=data, context=self.context)
        if not serializer.is_valid():
            self.fail('invalid')
        return serializer.save()

    def _handle_nested_update(self, data, lookup_value):
        """Update an existing object with nested data."""
        try:
            instance = self.queryset.get(**{self.lookup_field: lookup_value})
            serializer = self.serializer_class(
                instance, 
                data=data, 
                partial=True, 
                context=self.context
            )
            if not serializer.is_valid():
                self.fail('invalid')
            return serializer.save()
        except self.queryset.model.DoesNotExist:
            # If object doesn't exist, create it
            return self._handle_nested_create(data)

    def _handle_id_input(self, data):
        """Handle ID-based lookup."""
        try:
            return self.queryset.get(**{self.lookup_field: data})
        except self.queryset.model.DoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (ValueError, TypeError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def _handle_slug_input(self, data):
        """Handle slug-based lookup."""
        slug_field = 'slug' if hasattr(self.queryset.model, 'slug') else 'name'
        try:
            return self.queryset.get(**{slug_field: data})
        except self.queryset.model.DoesNotExist:
            self.fail('does_not_exist', pk_value=data)
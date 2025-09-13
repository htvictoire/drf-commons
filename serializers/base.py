"""
Base serializers for common functionality.

This module contains fundamental serializers that provide core functionality
like user context, selective field serialization, and common patterns.
"""

from typing import Dict, List, Optional, Set, Union, Any
from rest_framework import serializers
from rest_framework.request import Request
from django.contrib.auth import get_user_model
from django.db import models

from ..current_user.utils import get_current_authenticated_user

User = get_user_model()


class ContextualSerializerMixin:
    """
    Mixin that provides enhanced context handling and user access.
    
    Provides easy access to request, user, and other context data
    similar to how models have access to current user.
    """
    
    @property
    def request(self) -> Optional[Request]:
        """Get the current request from context."""
        return self.context.get('request')
    
    @property 
    def user(self) -> Optional[User]:
        """Get the current authenticated user from context or middleware."""
        if self.request and hasattr(self.request, 'user'):
            return self.request.user if self.request.user.is_authenticated else None
        return get_current_authenticated_user()
    
    def get_context_value(self, key: str, default: Any = None) -> Any:
        """Safely get a value from the serializer context."""
        return self.context.get(key, default)


class SelectiveFieldMixin:
    """
    Mixin that provides selective field inclusion/exclusion capabilities.
    
    Allows dynamic field selection based on query parameters, user permissions,
    or other runtime conditions.
    """
    
    def __init__(self, *args, **kwargs):
        # Remove custom kwargs before calling super
        dynamic_fields = kwargs.pop('fields', None)
        exclude_fields = kwargs.pop('exclude_fields', None)
        super().__init__(*args, **kwargs)
        
        if dynamic_fields is not None:
            self._filter_fields(include=dynamic_fields)
        
        if exclude_fields is not None:
            self._filter_fields(exclude=exclude_fields)
            
        # Handle query parameter field selection
        self._handle_query_field_selection()
    
    def _filter_fields(self, include: List[str] = None, exclude: List[str] = None):
        """
        Dynamically include or exclude fields.
        
        Args:
            include: List of field names to include (excludes all others)
            exclude: List of field names to exclude
        """
        existing_fields = set(self.fields.keys())
        
        if include is not None:
            # Only keep specified fields
            include_set = set(include) & existing_fields
            for field_name in existing_fields - include_set:
                self.fields.pop(field_name, None)
        
        if exclude is not None:
            # Remove specified fields
            for field_name in exclude:
                self.fields.pop(field_name, None)
    
    def _handle_query_field_selection(self):
        """Handle field selection from query parameters."""
        request = getattr(self, 'request', None) or self.context.get('request')
        if not request:
            return
            
        # Handle ?fields=field1,field2 parameter
        fields_param = request.query_params.get('fields')
        if fields_param:
            requested_fields = [f.strip() for f in fields_param.split(',')]
            self._filter_fields(include=requested_fields)
        
        # Handle ?exclude=field1,field2 parameter  
        exclude_param = request.query_params.get('exclude')
        if exclude_param:
            exclude_fields = [f.strip() for f in exclude_param.split(',')]
            self._filter_fields(exclude=exclude_fields)


class ValidationMixin:
    """
    Mixin that provides enhanced validation capabilities.
    
    Adds support for conditional validation, cross-field validation,
    and user-specific validation rules.
    """
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced validation with cross-field and user-specific checks.
        
        Args:
            attrs: Dictionary of field values to validate
            
        Returns:
            Validated attributes dictionary
        """
        attrs = super().validate(attrs)
        
        # Run cross-field validation
        attrs = self._validate_cross_fields(attrs)
        
        # Run user-specific validation
        attrs = self._validate_user_permissions(attrs)
        
        return attrs
    
    def _validate_cross_fields(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Override this method to add cross-field validation logic.
        
        Args:
            attrs: Dictionary of field values
            
        Returns:
            Validated attributes dictionary
        """
        return attrs
    
    def _validate_user_permissions(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Override this method to add user permission validation.
        
        Args:
            attrs: Dictionary of field values
            
        Returns:
            Validated attributes dictionary
        """
        return attrs
    
    def validate_field_permissions(self, field_name: str, value: Any) -> Any:
        """
        Validate if current user has permission to modify a specific field.
        
        Args:
            field_name: Name of the field being validated
            value: Value being set for the field
            
        Returns:
            Validated field value
            
        Raises:
            ValidationError: If user lacks permission
        """
        # Override in subclasses for specific permission logic
        return value


class AbstractBaseSerializer(ContextualSerializerMixin, SelectiveFieldMixin, ValidationMixin, serializers.ModelSerializer):
    """
    Abstract base serializer that provides common functionality for all model serializers.
    
    Combines multiple mixins to provide:
    - Enhanced context handling with easy access to request and user
    - Selective field inclusion/exclusion
    - Enhanced validation capabilities
    - Consistent serialization patterns
    
    This is similar to AbstractBaseModel but for serializers.
    """
    
    class Meta:
        abstract = True
    
    def __init__(self, *args, **kwargs):
        if type(self) is AbstractBaseSerializer:
            raise NotImplementedError("AbstractBaseSerializer is an abstract class and cannot be instantiated directly.")
        super().__init__(*args, **kwargs)
    
    def to_representation(self, instance: models.Model) -> Dict[str, Any]:
        """
        Enhanced representation method with common transformations.
        
        Args:
            instance: Model instance to serialize
            
        Returns:
            Dictionary representation of the instance
        """
        data = super().to_representation(instance)
        
        # Add common computed fields if they don't exist
        self._add_computed_fields(instance, data)
        
        return data
    
    def _add_computed_fields(self, instance: models.Model, data: Dict[str, Any]) -> None:
        """
        Add computed fields to the serialized data.
        
        Override this method in subclasses to add model-specific computed fields.
        
        Args:
            instance: Model instance being serialized
            data: Current serialized data dictionary
        """
        pass
    
    def get_field_names(self, declared_fields: Dict[str, serializers.Field], info) -> List[str]:
        """
        Enhanced field name resolution with better defaults.
        
        Args:
            declared_fields: Explicitly declared fields
            info: Model info from DRF
            
        Returns:
            List of field names to include
        """
        field_names = super().get_field_names(declared_fields, info)
        
        # Remove common fields that are usually not needed in API responses
        # but can be included explicitly if needed
        auto_exclude = getattr(self.Meta, 'auto_exclude_fields', [])
        if auto_exclude:
            field_names = [name for name in field_names if name not in auto_exclude]
        
        return field_names
    
    def __repr__(self) -> str:
        """Enhanced string representation."""
        model_name = self.Meta.model.__name__ if self.Meta.model else 'Unknown'
        field_count = len(self.fields)
        return f"<{self.__class__.__name__}(model={model_name}, fields={field_count})>"


class ReadOnlyBaseSerializer(AbstractBaseSerializer):
    """
    Base serializer for read-only operations.
    
    Useful for API endpoints that only return data without accepting input.
    All fields are automatically set to read-only.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields read-only
        for field in self.fields.values():
            field.read_only = True
    
    def create(self, validated_data: Dict[str, Any]) -> models.Model:
        """Read-only serializer should not support creation."""
        raise NotImplementedError("ReadOnlyBaseSerializer does not support create operations.")
    
    def update(self, instance: models.Model, validated_data: Dict[str, Any]) -> models.Model:
        """Read-only serializer should not support updates."""
        raise NotImplementedError("ReadOnlyBaseSerializer does not support update operations.")


class WriteOnlyBaseSerializer(AbstractBaseSerializer):
    """
    Base serializer for write-only operations.
    
    Useful for API endpoints that accept data but don't return full object representation.
    Commonly used for bulk operations or data ingestion endpoints.
    """
    
    def to_representation(self, instance: models.Model) -> Dict[str, Any]:
        """Return minimal representation for write-only operations."""
        # Only return essential fields like ID and success indicators
        essential_fields = getattr(self.Meta, 'essential_fields', ['id'])
        data = super().to_representation(instance)
        return {field: data.get(field) for field in essential_fields if field in data}
"""
Common serializers package.

This package provides reusable serializers, mixins, and field types for Django REST Framework.
It's organized into logical modules for better maintainability and easier imports.

Modules:
    base: Core serializer mixins and base classes (AbstractBaseSerializer, ContextualSerializerMixin)
    core: Core configurable field implementations (ConfigurableRelatedField, ConfigurableManyToManyField)
    mixins: Reusable mixins for field functionality (ConfigurableRelatedFieldMixin)
    related: Pre-configured field types for common use cases (IdToDataField, DataToIdField, etc.)

Usage:
    # Base serializers
    from common.serializers import AbstractBaseSerializer, ReadOnlyBaseSerializer
    from common.serializers import ContextualSerializerMixin, SelectiveFieldMixin
    
    # Core configurable fields
    from common.serializers import ConfigurableRelatedField, ConfigurableManyToManyField
    
    # Pre-configured field types
    from common.serializers import IdToDataField, DataToIdField, FlexibleField
    from common.serializers import ManyIdToDataField, ManyDataToIdField
    from common.serializers import ReadOnlyIdField, ReadOnlyStrField
"""

# Base serializers and mixins
from .base import (
    AbstractBaseSerializer,
    ContextualSerializerMixin,
    ReadOnlyBaseSerializer,
    SelectiveFieldMixin,
    ValidationMixin,
    WriteOnlyBaseSerializer,
)

# Core configurable fields
from .core import (
    ConfigurableRelatedField,
    ConfigurableManyToManyField,
    ReadOnlyRelatedField,
    WriteOnlyRelatedField,
)

# Pre-configured field types for common use cases
from .related import (
    # Single related fields
    IdToDataField,
    IdToStrField,
    DataToIdField,
    DataToStrField,
    DataToDataField,
    StrToDataField,
    IdOnlyField,
    StrOnlyField,
    FlexibleField,
    CustomOutputField,
    
    # Many-to-many fields
    ManyIdToDataField,
    ManyDataToIdField,
    ManyStrToDataField,
    ManyIdOnlyField,
    ManyStrOnlyField,
    ManyFlexibleField,
    
    # Read-only fields
    ReadOnlyIdField,
    ReadOnlyStrField,
    ReadOnlyDataField,
    ReadOnlyCustomField,
)

# Core mixin for custom implementations
from .mixins import ConfigurableRelatedFieldMixin

__all__ = [
    # Base serializers and mixins
    'AbstractBaseSerializer',
    'ReadOnlyBaseSerializer',
    'WriteOnlyBaseSerializer',
    'ContextualSerializerMixin',
    'SelectiveFieldMixin',
    'ValidationMixin',
    
    # Core configurable fields
    'ConfigurableRelatedField',
    'ConfigurableManyToManyField',
    'ReadOnlyRelatedField',
    'WriteOnlyRelatedField',
    'ConfigurableRelatedFieldMixin',
    
    # Pre-configured single related fields
    'IdToDataField',
    'IdToStrField',
    'DataToIdField',
    'DataToStrField',
    'DataToDataField',
    'StrToDataField',
    'IdOnlyField',
    'StrOnlyField',
    'FlexibleField',
    'CustomOutputField',
    
    # Pre-configured many-to-many fields
    'ManyIdToDataField',
    'ManyDataToIdField',
    'ManyStrToDataField',
    'ManyIdOnlyField',
    'ManyStrOnlyField',
    'ManyFlexibleField',
    
    # Pre-configured read-only fields
    'ReadOnlyIdField',
    'ReadOnlyStrField',
    'ReadOnlyDataField',
    'ReadOnlyCustomField',
]
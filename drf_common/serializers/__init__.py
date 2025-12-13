"""
Common serializers package.

This package provides configurable field types for Django REST Framework.
Fields are organized by functionality for better maintainability.

Modules:
    fields: Configurable field implementations
        - base: Core configurable field classes
        - single: Single related field types
        - many: Many-to-many field types
        - readonly: Read-only field types
        - custom: Custom/flexible field types
        - mixins: Core mixins for field functionality

Usage:
    # Core configurable fields
    from drf_common.serializers import ConfigurableRelatedField, ConfigurableManyToManyField

    # Pre-configured field types
    from drf_common.serializers import IdToDataField, DataToIdField, FlexibleField
    from drf_common.serializers import ManyIdToDataField, ManyDataToIdField
    from drf_common.serializers import ReadOnlyIdField, ReadOnlyStrField
"""

# Pre-configured field types
# Core configurable fields
from .fields import (  # Single related fields; Many-to-many fields; Read-only fields
    ConfigurableManyToManyField,
    ConfigurableRelatedField,
    CustomOutputField,
    DataToDataField,
    DataToIdField,
    DataToStrField,
    FlexibleField,
    IdOnlyField,
    IdToDataField,
    IdToStrField,
    ManyDataToIdField,
    ManyFlexibleField,
    ManyIdOnlyField,
    ManyIdToDataField,
    ManyStrOnlyField,
    ManyStrToDataField,
    ReadOnlyCustomField,
    ReadOnlyDataField,
    ReadOnlyIdField,
    ReadOnlyRelatedField,
    ReadOnlyStrField,
    StrOnlyField,
    StrToDataField,
    WriteOnlyRelatedField,
)

# Core mixin for custom implementations
from .fields.mixins import ConfigurableRelatedFieldMixin

# Base serializers for bulk operations
from .base import BaseModelSerializer, BulkUpdateListSerializer

__all__ = [
    # Core configurable fields
    "ConfigurableRelatedField",
    "ConfigurableManyToManyField",
    "ReadOnlyRelatedField",
    "WriteOnlyRelatedField",
    "ConfigurableRelatedFieldMixin",
    # Base serializers for bulk operations
    "BaseModelSerializer",
    "BulkUpdateListSerializer",
    # Single related fields
    "IdToDataField",
    "IdToStrField",
    "DataToIdField",
    "DataToStrField",
    "DataToDataField",
    "StrToDataField",
    "IdOnlyField",
    "StrOnlyField",
    "FlexibleField",
    "CustomOutputField",
    # Many-to-many fields
    "ManyIdToDataField",
    "ManyDataToIdField",
    "ManyStrToDataField",
    "ManyIdOnlyField",
    "ManyStrOnlyField",
    "ManyFlexibleField",
    # Read-only fields
    "ReadOnlyIdField",
    "ReadOnlyStrField",
    "ReadOnlyDataField",
    "ReadOnlyCustomField",
]

"""
Fields package for serializers.

This package provides configurable related fields organized by functionality:
- base: Core configurable field classes
- single: Single related field types for common use cases
- many: Many-to-many field types for common use cases
- readonly: Read-only field types for common use cases
- custom: Custom and flexible field types for advanced use cases
"""

# Core configurable fields
from .base import (
    ConfigurableManyToManyField,
    ConfigurableRelatedField,
    ReadOnlyRelatedField,
    WriteOnlyRelatedField,
)

# Custom/flexible fields
from .custom import (
    CustomOutputField,
    FlexibleField,
)

# Many-to-many fields
from .many import (
    ManyDataToIdField,
    ManyFlexibleField,
    ManyIdOnlyField,
    ManyIdToDataField,
    ManyStrOnlyField,
    ManyStrToDataField,
)

# Read-only fields
from .readonly import (
    ReadOnlyCustomField,
    ReadOnlyDataField,
    ReadOnlyIdField,
    ReadOnlyStrField,
)

# Single related fields
from .single import (
    DataToDataField,
    DataToIdField,
    DataToStrField,
    IdOnlyField,
    IdToDataField,
    IdToStrField,
    StrOnlyField,
    StrToDataField,
)

__all__ = [
    # Core configurable fields
    "ConfigurableRelatedField",
    "ConfigurableManyToManyField",
    "ReadOnlyRelatedField",
    "WriteOnlyRelatedField",
    # Single related fields
    "IdToDataField",
    "IdToStrField",
    "DataToIdField",
    "DataToStrField",
    "DataToDataField",
    "StrToDataField",
    "IdOnlyField",
    "StrOnlyField",
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
    # Custom/flexible fields
    "FlexibleField",
    "CustomOutputField",
]

"""
Common filters package.

This package provides comprehensive filtering capabilities for Django REST Framework
with operational filters, logical connectors, and range filters.

The package is organized into focused subpackages for better maintainability:

Subpackages:
    core: Main filter system components (AutoFilterSet, AutoFilterBackend, LogicalFilter)
    operators: Field-specific operator configurations organized by field type
    ranges: Range filter implementations (DateRangeFilter, NumericRangeFilter, etc.)

Modules:
    convenience: Pre-configured field filters for quick setup

Usage:
    # Main filtering system (recommended)
    from common.filters import AutoFilterBackend, AutoFilterSet
    
    # Logical filtering and range filters
    from common.filters import LogicalFilter, ComplexFilterSet
    from common.filters import DateRangeFilter, NumericRangeFilter, TimeRangeFilter, MultipleRangeFilter
    
    # Pre-configured field filters
    from common.filters import TextFieldFilters, NumericFieldFilters, DateFieldFilters
    
    # Core types and configurations
    from common.filters import FilterOperator, LogicalOperator, OperationalFilterMapping

Examples:
    # In your ViewSet
    class MyModelViewSet(viewsets.ModelViewSet):
        queryset = MyModel.objects.all()
        filter_backends = [AutoFilterBackend]
        filter_fields = ['name', 'status', 'created_at']  # Optional: limit fields
        include_logical_filter = True  # Optional: enable/disable logical filter
        include_range_filters = True  # Optional: enable/disable range filters
        include_multiple_range_filters = True  # Optional: enable/disable multiple ranges
    
    # URL filtering examples:
    # Basic operators: ?name__icontains=john&age__gte=18&status__exact=active
    # Range filters: ?created_at__range=2023-01-01,2023-12-31&price__range=100,500
    # Multiple ranges: ?age__multi_range={"or":[{"from":18,"to":25},{"from":60,"to":99}]}
    # Logical combinations: ?logical={"and":[{"name__icontains":"john"},{"age__gte":18}]}
    # Complex logical: ?logical={"or":[{"and":[{"age__gte":18},{"status":"active"}]},{"vip":true}]}
"""

# Main filtering system
from .core import (
    AutoFilterSet,
    AutoFilterBackend,
    LogicalFilter,
    ComplexFilterSet,
    FilterOperator,
    LogicalOperator,
    OperationalFilterConfig,
)

# Range filters
from .ranges import (
    DateRangeFilter,
    NumericRangeFilter,
    TimeRangeFilter,
    MultipleRangeFilter,
)

# Convenience filters
from .convenience import (
    TextFieldFilters,
    NumericFieldFilters,
    DateFieldFilters,
)

# Field mapping
from .operators.mapping import OperationalFilterMapping


#Ordering
from .ordering import ComputedOrderingFilter


__all__ = [
    # Main filtering system
    'AutoFilterSet',
    'AutoFilterBackend',
    'LogicalFilter',
    'ComplexFilterSet',
    
    # Core types
    'FilterOperator',
    'LogicalOperator',
    'OperationalFilterConfig',
    'OperationalFilterMapping',
    
    # Range filters
    'DateRangeFilter',
    'NumericRangeFilter',
    'TimeRangeFilter',
    'MultipleRangeFilter',
    
    # Convenience filters
    'TextFieldFilters',
    'NumericFieldFilters', 
    'DateFieldFilters',
    
    #Ordering
    'ComputedOrderingFilter'
]
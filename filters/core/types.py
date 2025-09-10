"""
Core types and enums for the filter system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Type
from django_filters import rest_framework as django_filters


class FilterOperator(Enum):
    """Enumeration of supported filter operators."""
    
    # Equality operators
    EXACT = "exact"
    NOT_EXACT = "not_exact"
    
    # Comparison operators
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    
    # Text operators
    CONTAINS = "contains"
    ICONTAINS = "icontains"
    STARTSWITH = "startswith"
    ISTARTSWITH = "istartswith"
    ENDSWITH = "endswith"
    IENDSWITH = "iendswith"
    REGEX = "regex"
    IREGEX = "iregex"
    
    # Null/Empty operators
    IS_NULL = "isnull"
    IS_EMPTY = "isempty"
    
    # Range operators
    RANGE = "range"
    IN = "in"
    NOT_IN = "not_in"
    
    # Array/JSON operations
    OVERLAP = "overlap"
    CONTAINED_BY = "contained_by"
    CONTAINS_ARRAY = "contains"
    HAS_KEY = "has_key"
    HAS_KEYS = "has_keys"
    HAS_ANY_KEYS = "has_any_keys"
    
    # Full-text search
    SEARCH = "search"
    
    # Time specific
    TIME = "time"
    HOUR = "hour"
    MINUTE = "minute"
    SECOND = "second"
    
    # Date/Time specific
    DATE = "date"
    YEAR = "year"
    MONTH = "month"
    DAY = "day"
    WEEK = "week"
    WEEK_DAY = "week_day"
    QUARTER = "quarter"


class LogicalOperator(Enum):
    """Enumeration of logical operators."""
    
    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class OperationalFilterConfig:
    """Configuration for an operational filter."""
    
    operator: FilterOperator
    field_class: Type[django_filters.Filter]
    label: str
    help_text: str
    supports_multiple: bool = False
    requires_special_handling: bool = False
"""
Convenience filter classes for common field types.

These classes provide pre-configured filters for quick setup without
needing to use the full auto-generation system.
"""

from django_filters import rest_framework as django_filters
from .ranges import DateRangeFilter, NumericRangeFilter, MultipleRangeFilter


class TextFieldFilters:
    """Pre-configured filters for text fields with all text operators."""
    
    @classmethod
    def for_field(cls, field_name: str, verbose_name: str = None):
        """Create comprehensive text filters for a specific field."""
        verbose_name = verbose_name or field_name.replace('_', ' ').title()
        
        return {
            f"{field_name}__exact": django_filters.CharFilter(
                field_name=field_name, lookup_expr='exact',
                label=f"{verbose_name} Equals",
                help_text=f"Exact match for {verbose_name} (case sensitive)"
            ),
            f"{field_name}__iexact": django_filters.CharFilter(
                field_name=field_name, lookup_expr='iexact',
                label=f"{verbose_name} Equals (case insensitive)",
                help_text=f"Exact match for {verbose_name} (case insensitive)"
            ),
            f"{field_name}__contains": django_filters.CharFilter(
                field_name=field_name, lookup_expr='contains',
                label=f"{verbose_name} Contains",
                help_text=f"{verbose_name} contains text (case sensitive)"
            ),
            f"{field_name}__icontains": django_filters.CharFilter(
                field_name=field_name, lookup_expr='icontains',
                label=f"{verbose_name} Contains (case insensitive)",
                help_text=f"{verbose_name} contains text (case insensitive)"
            ),
            f"{field_name}__startswith": django_filters.CharFilter(
                field_name=field_name, lookup_expr='startswith',
                label=f"{verbose_name} Starts With",
                help_text=f"{verbose_name} starts with text (case sensitive)"
            ),
            f"{field_name}__istartswith": django_filters.CharFilter(
                field_name=field_name, lookup_expr='istartswith',
                label=f"{verbose_name} Starts With (case insensitive)",
                help_text=f"{verbose_name} starts with text (case insensitive)"
            ),
            f"{field_name}__endswith": django_filters.CharFilter(
                field_name=field_name, lookup_expr='endswith',
                label=f"{verbose_name} Ends With",
                help_text=f"{verbose_name} ends with text (case sensitive)"
            ),
            f"{field_name}__iendswith": django_filters.CharFilter(
                field_name=field_name, lookup_expr='iendswith',
                label=f"{verbose_name} Ends With (case insensitive)",
                help_text=f"{verbose_name} ends with text (case insensitive)"
            ),
        }


class NumericFieldFilters:
    """Pre-configured filters for numeric fields with all comparison operators."""
    
    @classmethod
    def for_field(cls, field_name: str, verbose_name: str = None):
        """Create comprehensive numeric filters for a specific field."""
        verbose_name = verbose_name or field_name.replace('_', ' ').title()
        
        return {
            f"{field_name}__exact": django_filters.NumberFilter(
                field_name=field_name, lookup_expr='exact',
                label=f"{verbose_name} Equals (=)",
                help_text=f"Exact numeric match for {verbose_name}"
            ),
            f"{field_name}__gt": django_filters.NumberFilter(
                field_name=field_name, lookup_expr='gt',
                label=f"{verbose_name} Greater Than (>)",
                help_text=f"{verbose_name} is greater than specified value"
            ),
            f"{field_name}__gte": django_filters.NumberFilter(
                field_name=field_name, lookup_expr='gte',
                label=f"{verbose_name} Greater Than or Equal (≥)",
                help_text=f"{verbose_name} is greater than or equal to specified value"
            ),
            f"{field_name}__lt": django_filters.NumberFilter(
                field_name=field_name, lookup_expr='lt',
                label=f"{verbose_name} Less Than (<)",
                help_text=f"{verbose_name} is less than specified value"
            ),
            f"{field_name}__lte": django_filters.NumberFilter(
                field_name=field_name, lookup_expr='lte',
                label=f"{verbose_name} Less Than or Equal (≤)",
                help_text=f"{verbose_name} is less than or equal to specified value"
            ),
            f"{field_name}__range": NumericRangeFilter(
                field_name=field_name,
                label=f"{verbose_name} Range",
                help_text=f"{verbose_name} is within specified range (from,to)"
            ),
            f"{field_name}__multi_range": MultipleRangeFilter(
                field_name=field_name,
                label=f"{verbose_name} Multiple Ranges",
                help_text=f"{verbose_name} matches multiple ranges with AND/OR logic"
            ),
        }


class DateFieldFilters:
    """Pre-configured filters for date fields with all date operators."""
    
    @classmethod
    def for_field(cls, field_name: str, verbose_name: str = None):
        """Create comprehensive date filters for a specific field."""
        verbose_name = verbose_name or field_name.replace('_', ' ').title()
        
        return {
            f"{field_name}__exact": django_filters.DateFilter(
                field_name=field_name, lookup_expr='exact',
                label=f"{verbose_name} Equals",
                help_text=f"Exact date match for {verbose_name}"
            ),
            f"{field_name}__gt": django_filters.DateFilter(
                field_name=field_name, lookup_expr='gt',
                label=f"{verbose_name} After (>)",
                help_text=f"{verbose_name} is after specified date"
            ),
            f"{field_name}__gte": django_filters.DateFilter(
                field_name=field_name, lookup_expr='gte',
                label=f"{verbose_name} After or On (≥)",
                help_text=f"{verbose_name} is after or equal to specified date"
            ),
            f"{field_name}__lt": django_filters.DateFilter(
                field_name=field_name, lookup_expr='lt',
                label=f"{verbose_name} Before (<)",
                help_text=f"{verbose_name} is before specified date"
            ),
            f"{field_name}__lte": django_filters.DateFilter(
                field_name=field_name, lookup_expr='lte',
                label=f"{verbose_name} Before or On (≤)",
                help_text=f"{verbose_name} is before or equal to specified date"
            ),
            f"{field_name}__range": DateRangeFilter(
                field_name=field_name,
                label=f"{verbose_name} Range",
                help_text=f"{verbose_name} is within specified date range (from,to)"
            ),
            f"{field_name}__multi_range": MultipleRangeFilter(
                field_name=field_name,
                label=f"{verbose_name} Multiple Ranges",
                help_text=f"{verbose_name} matches multiple date ranges with AND/OR logic"
            ),
            f"{field_name}__year": django_filters.NumberFilter(
                field_name=field_name, lookup_expr='year',
                label=f"{verbose_name} Year",
                help_text=f"Filter {verbose_name} by year"
            ),
            f"{field_name}__month": django_filters.NumberFilter(
                field_name=field_name, lookup_expr='month',
                label=f"{verbose_name} Month",
                help_text=f"Filter {verbose_name} by month (1-12)"
            ),
            f"{field_name}__day": django_filters.NumberFilter(
                field_name=field_name, lookup_expr='day',
                label=f"{verbose_name} Day",
                help_text=f"Filter {verbose_name} by day of month (1-31)"
            ),
        }
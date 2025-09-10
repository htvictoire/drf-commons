"""
Date and time field operators (DateField, DateTimeField, TimeField).
"""

from typing import Dict
from django_filters import rest_framework as django_filters

from ..core.types import FilterOperator, OperationalFilterConfig


def get_date_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for date fields."""
    return {
        FilterOperator.EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.EXACT,
            field_class=django_filters.DateFilter,
            label="Equals (=)",
            help_text="Exact date match"
        ),
        FilterOperator.NOT_EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.NOT_EXACT,
            field_class=django_filters.DateFilter,
            label="Not equals (≠)",
            help_text="Exclude exact date match",
            requires_special_handling=True
        ),
        FilterOperator.GREATER_THAN.value: OperationalFilterConfig(
            operator=FilterOperator.GREATER_THAN,
            field_class=django_filters.DateFilter,
            label="After (>)",
            help_text="Date is after specified date"
        ),
        FilterOperator.GREATER_THAN_OR_EQUAL.value: OperationalFilterConfig(
            operator=FilterOperator.GREATER_THAN_OR_EQUAL,
            field_class=django_filters.DateFilter,
            label="After or on (≥)",
            help_text="Date is after or equal to specified date"
        ),
        FilterOperator.LESS_THAN.value: OperationalFilterConfig(
            operator=FilterOperator.LESS_THAN,
            field_class=django_filters.DateFilter,
            label="Before (<)",
            help_text="Date is before specified date"
        ),
        FilterOperator.LESS_THAN_OR_EQUAL.value: OperationalFilterConfig(
            operator=FilterOperator.LESS_THAN_OR_EQUAL,
            field_class=django_filters.DateFilter,
            label="Before or on (≤)",
            help_text="Date is before or equal to specified date"
        ),
        FilterOperator.IS_NULL.value: OperationalFilterConfig(
            operator=FilterOperator.IS_NULL,
            field_class=django_filters.BooleanFilter,
            label="Is null",
            help_text="Field is null"
        ),
        FilterOperator.RANGE.value: OperationalFilterConfig(
            operator=FilterOperator.RANGE,
            field_class=django_filters.DateRangeFilter,
            label="Date range",
            help_text="Date is within specified range (from,to)",
            supports_multiple=True
        ),
        FilterOperator.YEAR.value: OperationalFilterConfig(
            operator=FilterOperator.YEAR,
            field_class=django_filters.NumberFilter,
            label="Year",
            help_text="Filter by year"
        ),
        FilterOperator.MONTH.value: OperationalFilterConfig(
            operator=FilterOperator.MONTH,
            field_class=django_filters.NumberFilter,
            label="Month",
            help_text="Filter by month (1-12)"
        ),
        FilterOperator.DAY.value: OperationalFilterConfig(
            operator=FilterOperator.DAY,
            field_class=django_filters.NumberFilter,
            label="Day",
            help_text="Filter by day of month (1-31)"
        ),
        FilterOperator.WEEK.value: OperationalFilterConfig(
            operator=FilterOperator.WEEK,
            field_class=django_filters.NumberFilter,
            label="Week",
            help_text="Filter by week of year (1-53)"
        ),
        FilterOperator.WEEK_DAY.value: OperationalFilterConfig(
            operator=FilterOperator.WEEK_DAY,
            field_class=django_filters.NumberFilter,
            label="Weekday",
            help_text="Filter by day of week (1=Sunday, 7=Saturday)"
        ),
        FilterOperator.QUARTER.value: OperationalFilterConfig(
            operator=FilterOperator.QUARTER,
            field_class=django_filters.NumberFilter,
            label="Quarter",
            help_text="Filter by quarter (1-4)"
        ),
    }


def get_datetime_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for datetime fields."""
    date_ops = get_date_operators()
    datetime_ops = {}
    
    for key, config in date_ops.items():
        if config.field_class == django_filters.DateFilter:
            datetime_ops[key] = OperationalFilterConfig(
                operator=config.operator,
                field_class=django_filters.DateTimeFilter,
                label=config.label.replace("Date", "DateTime"),
                help_text=config.help_text.replace("date", "datetime"),
                supports_multiple=config.supports_multiple,
                requires_special_handling=config.requires_special_handling
            )
        elif config.field_class == django_filters.DateRangeFilter:
            datetime_ops[key] = OperationalFilterConfig(
                operator=config.operator,
                field_class=django_filters.DateTimeFromToRangeFilter,
                label="DateTime range",
                help_text="DateTime is within specified range (from,to)",
                supports_multiple=True
            )
        else:
            datetime_ops[key] = config
    
    return datetime_ops


def get_time_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for time fields."""
    return {
        FilterOperator.EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.EXACT,
            field_class=django_filters.TimeFilter,
            label="Equals (=)",
            help_text="Exact time match"
        ),
        FilterOperator.NOT_EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.NOT_EXACT,
            field_class=django_filters.TimeFilter,
            label="Not equals (≠)",
            help_text="Exclude exact time match",
            requires_special_handling=True
        ),
        FilterOperator.GREATER_THAN.value: OperationalFilterConfig(
            operator=FilterOperator.GREATER_THAN,
            field_class=django_filters.TimeFilter,
            label="After (>)",
            help_text="Time is after specified time"
        ),
        FilterOperator.GREATER_THAN_OR_EQUAL.value: OperationalFilterConfig(
            operator=FilterOperator.GREATER_THAN_OR_EQUAL,
            field_class=django_filters.TimeFilter,
            label="After or at (≥)",
            help_text="Time is after or equal to specified time"
        ),
        FilterOperator.LESS_THAN.value: OperationalFilterConfig(
            operator=FilterOperator.LESS_THAN,
            field_class=django_filters.TimeFilter,
            label="Before (<)",
            help_text="Time is before specified time"
        ),
        FilterOperator.LESS_THAN_OR_EQUAL.value: OperationalFilterConfig(
            operator=FilterOperator.LESS_THAN_OR_EQUAL,
            field_class=django_filters.TimeFilter,
            label="Before or at (≤)",
            help_text="Time is before or equal to specified time"
        ),
        FilterOperator.IS_NULL.value: OperationalFilterConfig(
            operator=FilterOperator.IS_NULL,
            field_class=django_filters.BooleanFilter,
            label="Is null",
            help_text="Field is null"
        ),
        FilterOperator.RANGE.value: OperationalFilterConfig(
            operator=FilterOperator.RANGE,
            field_class=django_filters.TimeRangeFilter,
            label="Time range",
            help_text="Time is within specified range (from,to)",
            supports_multiple=True
        ),
        FilterOperator.HOUR.value: OperationalFilterConfig(
            operator=FilterOperator.HOUR,
            field_class=django_filters.NumberFilter,
            label="Hour",
            help_text="Filter by hour (0-23)"
        ),
        FilterOperator.MINUTE.value: OperationalFilterConfig(
            operator=FilterOperator.MINUTE,
            field_class=django_filters.NumberFilter,
            label="Minute",
            help_text="Filter by minute (0-59)"
        ),
        FilterOperator.SECOND.value: OperationalFilterConfig(
            operator=FilterOperator.SECOND,
            field_class=django_filters.NumberFilter,
            label="Second",
            help_text="Filter by second (0-59)"
        ),
    }
"""
Numeric field operators (IntegerField, FloatField, DecimalField).
"""

from typing import Dict
from django_filters import rest_framework as django_filters

from ..core.types import FilterOperator, OperationalFilterConfig


def get_numeric_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for numeric fields."""
    return {
        FilterOperator.EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.EXACT,
            field_class=django_filters.NumberFilter,
            label="Equals (=)",
            help_text="Exact numeric match"
        ),
        FilterOperator.NOT_EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.NOT_EXACT,
            field_class=django_filters.NumberFilter,
            label="Not equals (≠)",
            help_text="Exclude exact numeric match",
            requires_special_handling=True
        ),
        FilterOperator.GREATER_THAN.value: OperationalFilterConfig(
            operator=FilterOperator.GREATER_THAN,
            field_class=django_filters.NumberFilter,
            label="Greater than (>)",
            help_text="Value is greater than specified number"
        ),
        FilterOperator.GREATER_THAN_OR_EQUAL.value: OperationalFilterConfig(
            operator=FilterOperator.GREATER_THAN_OR_EQUAL,
            field_class=django_filters.NumberFilter,
            label="Greater than or equal (≥)",
            help_text="Value is greater than or equal to specified number"
        ),
        FilterOperator.LESS_THAN.value: OperationalFilterConfig(
            operator=FilterOperator.LESS_THAN,
            field_class=django_filters.NumberFilter,
            label="Less than (<)",
            help_text="Value is less than specified number"
        ),
        FilterOperator.LESS_THAN_OR_EQUAL.value: OperationalFilterConfig(
            operator=FilterOperator.LESS_THAN_OR_EQUAL,
            field_class=django_filters.NumberFilter,
            label="Less than or equal (≤)",
            help_text="Value is less than or equal to specified number"
        ),
        FilterOperator.IS_NULL.value: OperationalFilterConfig(
            operator=FilterOperator.IS_NULL,
            field_class=django_filters.BooleanFilter,
            label="Is null",
            help_text="Field is null"
        ),
        FilterOperator.RANGE.value: OperationalFilterConfig(
            operator=FilterOperator.RANGE,
            field_class=django_filters.RangeFilter,
            label="Range",
            help_text="Value is within specified range (from,to)",
            supports_multiple=True
        ),
        FilterOperator.IN.value: OperationalFilterConfig(
            operator=FilterOperator.IN,
            field_class=django_filters.BaseInFilter,
            label="In list",
            help_text="Value is in the provided list",
            supports_multiple=True
        ),
        FilterOperator.NOT_IN.value: OperationalFilterConfig(
            operator=FilterOperator.NOT_IN,
            field_class=django_filters.BaseInFilter,
            label="Not in list",
            help_text="Value is not in the provided list",
            supports_multiple=True,
            requires_special_handling=True
        ),
    }


def get_decimal_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for decimal fields."""
    numeric_ops = get_numeric_operators()
    decimal_ops = {}
    
    for key, config in numeric_ops.items():
        if config.field_class == django_filters.NumberFilter:
            decimal_ops[key] = OperationalFilterConfig(
                operator=config.operator,
                field_class=django_filters.NumberFilter,  # NumberFilter works for decimals too
                label=config.label,
                help_text=config.help_text,
                supports_multiple=config.supports_multiple,
                requires_special_handling=config.requires_special_handling
            )
        else:
            decimal_ops[key] = config
    
    return decimal_ops
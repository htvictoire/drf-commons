"""
Special field operators (BooleanField, UUIDField, JSONField, ArrayField).
"""

from typing import Dict
from django_filters import rest_framework as django_filters

from ..core.types import FilterOperator, OperationalFilterConfig


def get_boolean_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for boolean fields."""
    return {
        FilterOperator.EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.EXACT,
            field_class=django_filters.BooleanFilter,
            label="Equals",
            help_text="Boolean value (true/false)"
        ),
        FilterOperator.IS_NULL.value: OperationalFilterConfig(
            operator=FilterOperator.IS_NULL,
            field_class=django_filters.BooleanFilter,
            label="Is null",
            help_text="Field is null"
        ),
    }


def get_uuid_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for UUID fields."""
    return {
        FilterOperator.EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.EXACT,
            field_class=django_filters.UUIDFilter,
            label="Equals",
            help_text="Exact UUID match"
        ),
        FilterOperator.NOT_EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.NOT_EXACT,
            field_class=django_filters.UUIDFilter,
            label="Not equals",
            help_text="Exclude exact UUID match",
            requires_special_handling=True
        ),
        FilterOperator.IS_NULL.value: OperationalFilterConfig(
            operator=FilterOperator.IS_NULL,
            field_class=django_filters.BooleanFilter,
            label="Is null",
            help_text="Field is null"
        ),
        FilterOperator.IN.value: OperationalFilterConfig(
            operator=FilterOperator.IN,
            field_class=django_filters.BaseInFilter,
            label="In list",
            help_text="UUID is in the provided list",
            supports_multiple=True
        ),
        FilterOperator.NOT_IN.value: OperationalFilterConfig(
            operator=FilterOperator.NOT_IN,
            field_class=django_filters.BaseInFilter,
            label="Not in list",
            help_text="UUID is not in the provided list",
            supports_multiple=True,
            requires_special_handling=True
        ),
    }


def get_json_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for JSON fields."""
    return {
        FilterOperator.EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.EXACT,
            field_class=django_filters.CharFilter,
            label="Equals",
            help_text="Exact JSON match"
        ),
        FilterOperator.IS_NULL.value: OperationalFilterConfig(
            operator=FilterOperator.IS_NULL,
            field_class=django_filters.BooleanFilter,
            label="Is null",
            help_text="Field is null"
        ),
        FilterOperator.HAS_KEY.value: OperationalFilterConfig(
            operator=FilterOperator.HAS_KEY,
            field_class=django_filters.CharFilter,
            label="Has key",
            help_text="JSON object has the specified key"
        ),
        FilterOperator.HAS_KEYS.value: OperationalFilterConfig(
            operator=FilterOperator.HAS_KEYS,
            field_class=django_filters.BaseInFilter,
            label="Has all keys",
            help_text="JSON object has all specified keys",
            supports_multiple=True
        ),
        FilterOperator.HAS_ANY_KEYS.value: OperationalFilterConfig(
            operator=FilterOperator.HAS_ANY_KEYS,
            field_class=django_filters.BaseInFilter,
            label="Has any keys",
            help_text="JSON object has any of the specified keys",
            supports_multiple=True
        ),
        FilterOperator.CONTAINS.value: OperationalFilterConfig(
            operator=FilterOperator.CONTAINS,
            field_class=django_filters.CharFilter,
            label="Contains",
            help_text="JSON contains the specified structure"
        ),
        FilterOperator.CONTAINED_BY.value: OperationalFilterConfig(
            operator=FilterOperator.CONTAINED_BY,
            field_class=django_filters.CharFilter,
            label="Contained by",
            help_text="JSON is contained by the specified structure"
        ),
    }


def get_array_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for array fields."""
    return {
        FilterOperator.EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.EXACT,
            field_class=django_filters.CharFilter,
            label="Equals",
            help_text="Exact array match"
        ),
        FilterOperator.IS_NULL.value: OperationalFilterConfig(
            operator=FilterOperator.IS_NULL,
            field_class=django_filters.BooleanFilter,
            label="Is null",
            help_text="Field is null"
        ),
        FilterOperator.CONTAINS.value: OperationalFilterConfig(
            operator=FilterOperator.CONTAINS,
            field_class=django_filters.CharFilter,
            label="Contains",
            help_text="Array contains the specified values"
        ),
        FilterOperator.CONTAINED_BY.value: OperationalFilterConfig(
            operator=FilterOperator.CONTAINED_BY,
            field_class=django_filters.CharFilter,
            label="Contained by",
            help_text="Array is contained by the specified values"
        ),
        FilterOperator.OVERLAP.value: OperationalFilterConfig(
            operator=FilterOperator.OVERLAP,
            field_class=django_filters.CharFilter,
            label="Overlaps",
            help_text="Array overlaps with the specified values"
        ),
    }
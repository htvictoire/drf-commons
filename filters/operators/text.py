"""
Text field operators (CharField, TextField, EmailField, URLField, SlugField).
"""

from typing import Dict
from django_filters import rest_framework as django_filters

from ..core.types import FilterOperator, OperationalFilterConfig


def get_text_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for text fields."""
    return {
        FilterOperator.EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.EXACT,
            field_class=django_filters.CharFilter,
            label="Equals",
            help_text="Exact text match (case sensitive)"
        ),
        FilterOperator.NOT_EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.NOT_EXACT,
            field_class=django_filters.CharFilter,
            label="Not equals",
            help_text="Exclude exact text match",
            requires_special_handling=True
        ),
        FilterOperator.CONTAINS.value: OperationalFilterConfig(
            operator=FilterOperator.CONTAINS,
            field_class=django_filters.CharFilter,
            label="Contains",
            help_text="Text contains substring (case sensitive)"
        ),
        FilterOperator.ICONTAINS.value: OperationalFilterConfig(
            operator=FilterOperator.ICONTAINS,
            field_class=django_filters.CharFilter,
            label="Contains (case insensitive)",
            help_text="Text contains substring (case insensitive)"
        ),
        FilterOperator.STARTSWITH.value: OperationalFilterConfig(
            operator=FilterOperator.STARTSWITH,
            field_class=django_filters.CharFilter,
            label="Starts with",
            help_text="Text starts with substring (case sensitive)"
        ),
        FilterOperator.ISTARTSWITH.value: OperationalFilterConfig(
            operator=FilterOperator.ISTARTSWITH,
            field_class=django_filters.CharFilter,
            label="Starts with (case insensitive)",
            help_text="Text starts with substring (case insensitive)"
        ),
        FilterOperator.ENDSWITH.value: OperationalFilterConfig(
            operator=FilterOperator.ENDSWITH,
            field_class=django_filters.CharFilter,
            label="Ends with",
            help_text="Text ends with substring (case sensitive)"
        ),
        FilterOperator.IENDSWITH.value: OperationalFilterConfig(
            operator=FilterOperator.IENDSWITH,
            field_class=django_filters.CharFilter,
            label="Ends with (case insensitive)",
            help_text="Text ends with substring (case insensitive)"
        ),
        FilterOperator.REGEX.value: OperationalFilterConfig(
            operator=FilterOperator.REGEX,
            field_class=django_filters.CharFilter,
            label="Regex match",
            help_text="Text matches regular expression (case sensitive)"
        ),
        FilterOperator.IREGEX.value: OperationalFilterConfig(
            operator=FilterOperator.IREGEX,
            field_class=django_filters.CharFilter,
            label="Regex match (case insensitive)",
            help_text="Text matches regular expression (case insensitive)"
        ),
        FilterOperator.IS_NULL.value: OperationalFilterConfig(
            operator=FilterOperator.IS_NULL,
            field_class=django_filters.BooleanFilter,
            label="Is null/empty",
            help_text="Field is null or empty"
        ),
        FilterOperator.IN.value: OperationalFilterConfig(
            operator=FilterOperator.IN,
            field_class=django_filters.CharFilter,
            label="In list",
            help_text="Text value is in the provided list (comma-separated)",
            supports_multiple=True
        ),
        FilterOperator.NOT_IN.value: OperationalFilterConfig(
            operator=FilterOperator.NOT_IN,
            field_class=django_filters.CharFilter,
            label="Not in list",
            help_text="Text value is not in the provided list (comma-separated)",
            supports_multiple=True,
            requires_special_handling=True
        ),
    }


def get_email_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for email fields."""
    return get_text_operators()


def get_url_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for URL fields."""
    return get_text_operators()


def get_slug_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for slug fields."""
    return get_text_operators()
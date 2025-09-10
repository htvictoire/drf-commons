"""
Related field operators (ForeignKey, OneToOneField, ManyToManyField).
"""

from typing import Dict
from django_filters import rest_framework as django_filters

from ..core.types import FilterOperator, OperationalFilterConfig


def get_foreignkey_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for foreign key fields."""
    return {
        FilterOperator.EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.EXACT,
            field_class=django_filters.ModelChoiceFilter,
            label="Equals",
            help_text="Related object equals specified value"
        ),
        FilterOperator.NOT_EXACT.value: OperationalFilterConfig(
            operator=FilterOperator.NOT_EXACT,
            field_class=django_filters.ModelChoiceFilter,
            label="Not equals",
            help_text="Related object does not equal specified value",
            requires_special_handling=True
        ),
        FilterOperator.IS_NULL.value: OperationalFilterConfig(
            operator=FilterOperator.IS_NULL,
            field_class=django_filters.BooleanFilter,
            label="Is null",
            help_text="Related object is null"
        ),
        FilterOperator.IN.value: OperationalFilterConfig(
            operator=FilterOperator.IN,
            field_class=django_filters.ModelMultipleChoiceFilter,
            label="In list",
            help_text="Related object is in the provided list",
            supports_multiple=True
        ),
        FilterOperator.NOT_IN.value: OperationalFilterConfig(
            operator=FilterOperator.NOT_IN,
            field_class=django_filters.ModelMultipleChoiceFilter,
            label="Not in list",
            help_text="Related object is not in the provided list",
            supports_multiple=True,
            requires_special_handling=True
        ),
    }


def get_manytomany_operators() -> Dict[str, OperationalFilterConfig]:
    """Get all supported operators for many-to-many fields."""
    return {
        FilterOperator.IN.value: OperationalFilterConfig(
            operator=FilterOperator.IN,
            field_class=django_filters.ModelMultipleChoiceFilter,
            label="Contains any",
            help_text="Contains any of the specified related objects",
            supports_multiple=True
        ),
        FilterOperator.NOT_IN.value: OperationalFilterConfig(
            operator=FilterOperator.NOT_IN,
            field_class=django_filters.ModelMultipleChoiceFilter,
            label="Excludes all",
            help_text="Does not contain any of the specified related objects",
            supports_multiple=True,
            requires_special_handling=True
        ),
        FilterOperator.IS_NULL.value: OperationalFilterConfig(
            operator=FilterOperator.IS_NULL,
            field_class=django_filters.BooleanFilter,
            label="Is empty",
            help_text="Has no related objects"
        ),
    }
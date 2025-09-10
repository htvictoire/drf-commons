"""
Field mapping utilities to determine which operators apply to which Django field types.
"""

from typing import Dict
from django.db import models
from django_filters import rest_framework as django_filters

from ..core.types import OperationalFilterConfig, FilterOperator
from . import (
    get_text_operators, get_email_operators, get_url_operators, get_slug_operators,
    get_numeric_operators, get_decimal_operators,
    get_date_operators, get_datetime_operators, get_time_operators,
    get_boolean_operators, get_uuid_operators, get_json_operators, get_array_operators,
    get_foreignkey_operators, get_manytomany_operators
)


class OperationalFilterMapping:
    """Maps Django field types to their supported operational filters."""
    
    @classmethod
    def get_field_operators(cls, field: models.Field) -> Dict[str, OperationalFilterConfig]:
        """Get appropriate operators for a given model field."""
        from django.db.models.fields import (
            CharField, TextField, IntegerField, FloatField, DecimalField,
            DateField, DateTimeField, TimeField, BooleanField, EmailField,
            URLField, SlugField, UUIDField
        )
        from django.db.models import JSONField
        from django.db.models.fields.related import ForeignKey, OneToOneField, ManyToManyField
        
        # Handle all Django field types
        if isinstance(field, (CharField, TextField)):
            return get_text_operators()
        elif isinstance(field, EmailField):
            return get_email_operators()
        elif isinstance(field, URLField):
            return get_url_operators()
        elif isinstance(field, SlugField):
            return get_slug_operators()
        elif isinstance(field, (IntegerField, FloatField)):
            return get_numeric_operators()
        elif isinstance(field, DecimalField):
            return get_decimal_operators()
        elif isinstance(field, DateField):
            return get_date_operators()
        elif isinstance(field, DateTimeField):
            return get_datetime_operators()
        elif isinstance(field, TimeField):
            return get_time_operators()
        elif isinstance(field, BooleanField):
            return get_boolean_operators()
        elif isinstance(field, UUIDField):
            return get_uuid_operators()
        elif isinstance(field, (ForeignKey, OneToOneField)):
            return get_foreignkey_operators()
        elif isinstance(field, ManyToManyField):
            return get_manytomany_operators()
        
        # Handle PostgreSQL-specific fields if available
        try:
            from django.contrib.postgres.fields import JSONField as PostgresJSONField
            from django.contrib.postgres.fields import ArrayField
            
            if isinstance(field, PostgresJSONField):
                return get_json_operators()
            elif isinstance(field, ArrayField):
                return get_array_operators()
        except ImportError:
            pass
        
        # Handle Django 3.1+ JSONField
        try:
            if isinstance(field, JSONField):
                return get_json_operators()
        except NameError:
            pass
        
        # Default to basic text operators for unrecognized fields
        return {
            FilterOperator.EXACT.value: OperationalFilterConfig(
                operator=FilterOperator.EXACT,
                field_class=django_filters.CharFilter,
                label="Equals",
                help_text=f"Exact match for {field.__class__.__name__} field"
            )
        }
"""
Main auto-generating FilterSet with comprehensive operational filters.
"""

from typing import Dict, List, Type, Optional
from django.db import models
from django_filters import rest_framework as django_filters
from rest_framework.exceptions import ValidationError

from .types import OperationalFilterConfig
from .logical import ComplexFilterSet, LogicalFilter
from ..operators.mapping import OperationalFilterMapping
from ..ranges import DateRangeFilter, NumericRangeFilter, TimeRangeFilter, MultipleRangeFilter


class AutoFilterSet(ComplexFilterSet):
    """
    Comprehensive auto-generating FilterSet with all operational filters.
    
    This FilterSet automatically generates filters with:
    - All comparison operators (=, !=, <, >, <=, >=)
    - Range filters for dates, times, and numbers (from/to values)
    - Multiple range filters with logical operators
    - Logical connectors (AND, OR, NOT)
    - Text search operators (contains, startswith, etc.)
    - Support for all Django field types
    """
    
    @classmethod
    def generate_filters(
        cls, 
        model_class: Type[models.Model], 
        field_names: Optional[List[str]] = None,
        include_logical: bool = True,
        include_ranges: bool = True,
        include_multiple_ranges: bool = True
    ) -> Dict[str, django_filters.Filter]:
        """
        Generate comprehensive filter fields for a model class.
        
        Args:
            model_class: The model class to generate filters for
            field_names: Optional list of field names to generate filters for
            include_logical: Whether to include logical filter
            include_ranges: Whether to include range filters
            include_multiple_ranges: Whether to include multiple range filters
            
        Returns:
            Dictionary of filter name to filter instance
        """
        filters = {}
        
        # Add logical filter if requested
        if include_logical:
            filters['logical'] = LogicalFilter(
                label="Logical Filter",
                help_text="Complex logical filter supporting AND, OR, NOT operations"
            )
        
        # Get all model fields
        model_fields = model_class._meta.get_fields()
        model_field_names = {field.name for field in model_fields if hasattr(field, 'name')}
        
        # Check for disabled fields (fields set to None in the model class)
        disabled_fields = set()
        for attr_name in dir(model_class):
            if not attr_name.startswith('_'):
                attr_value = getattr(model_class, attr_name, None)
                if attr_value is None and attr_name in model_field_names:
                    disabled_fields.add(attr_name)
        
        # Validate field names if provided
        if field_names is not None:
            invalid_fields = set(field_names) - model_field_names
            if invalid_fields:
                raise ValidationError(
                    f"Invalid field(s) in field_names: {', '.join(invalid_fields)}. "
                    f"Valid fields are: {', '.join(sorted(model_field_names))}"
                )
        
        # Process each field
        for field in model_fields:
            # Skip None fields (disabled inherited fields)
            if field is None:
                continue
                
            # Skip auto-created fields
            if getattr(field, 'auto_created', False):
                continue
            
            # Skip reverse relationships
            if getattr(field, 'one_to_many', False) or getattr(field, 'many_to_many', False):
                continue
            
            # Skip fields not in field_names if provided
            if field_names is not None and field.name not in field_names:
                continue
            
            # Skip disabled fields (fields set to None in the model class)
            if field.name in disabled_fields:
                continue
            
            # Generate operational filters for this field
            field_filters = cls._generate_field_filters(field, include_ranges, include_multiple_ranges)
            filters.update(field_filters)
        
        return filters
    
    @classmethod
    def _generate_field_filters(
        cls, 
        field: models.Field, 
        include_ranges: bool = True,
        include_multiple_ranges: bool = True
    ) -> Dict[str, django_filters.Filter]:
        """
        Generate all operational filters for a specific field.
        
        Args:
            field: The model field to generate filters for
            include_ranges: Whether to include range filters
            include_multiple_ranges: Whether to include multiple range filters
            
        Returns:
            Dictionary of filter instances for the field
        """
        filters = {}
        field_name = field.name
        verbose_name = getattr(field, 'verbose_name', field_name)
        
        # Get operational filter configurations for this field type
        operator_configs = OperationalFilterMapping.get_field_operators(field)
        
        # Generate filters for each operator
        for operator_key, config in operator_configs.items():
            filter_name = f"{field_name}__{operator_key}"
            
            # Create label and help text
            label = f"{verbose_name.capitalize()} {config.label}"
            help_text = config.help_text.replace("Filter by", f"Filter {verbose_name} by")
            
            # Handle special cases
            if config.requires_special_handling:
                filter_instance = cls._create_special_filter(
                    field, field_name, config, label, help_text
                )
            else:
                filter_instance = cls._create_standard_filter(
                    field, field_name, config, label, help_text
                )
            
            if filter_instance:
                filters[filter_name] = filter_instance
            else:
                # Skip filters that failed to create instead of breaking everything
                pass
        
        # Add range filters for applicable field types
        if include_ranges:
            range_filters = cls._generate_range_filters(field, verbose_name, include_multiple_ranges)
            filters.update(range_filters)
        
        return filters
    
    @classmethod
    def _create_standard_filter(
        cls,
        field: models.Field,
        field_name: str,
        config: OperationalFilterConfig,
        label: str,
        help_text: str
    ) -> Optional[django_filters.Filter]:
        """Create a standard filter instance."""
        from django.db.models.fields.related import ForeignKey, OneToOneField, ManyToManyField
        
        # Determine filter parameters
        filter_kwargs = {
            'field_name': field_name,
            'label': label,
            'help_text': help_text
        }
        
        # Add queryset for related fields when using Model filters
        if isinstance(field, (ForeignKey, OneToOneField, ManyToManyField)):
            if cls._filter_requires_queryset(config.field_class):
                try:
                    filter_kwargs['queryset'] = field.related_model.objects.all()
                except Exception:
                    # If queryset access fails, skip this filter
                    return None
        
        # Add lookup_expr for filters that support it (exclude range filters and CSV filters)
        if (config.operator.value not in ['range', 'in', 'not_in'] and 
            not issubclass(config.field_class, django_filters.BaseCSVFilter)):
            filter_kwargs['lookup_expr'] = config.operator.value
        
        try:
            return config.field_class(**filter_kwargs)
        except Exception:
            # If standard filter creation fails, return None instead of crashing
            return None
    
    @classmethod
    def _filter_requires_queryset(cls, filter_class) -> bool:
        """Check if a filter class requires a queryset parameter."""
        return issubclass(filter_class, (
            django_filters.ModelChoiceFilter, 
            django_filters.ModelMultipleChoiceFilter
        ))
    
    @classmethod
    def _create_special_filter(
        cls,
        field: models.Field,
        field_name: str,
        config: OperationalFilterConfig,
        label: str,
        help_text: str
    ) -> Optional[django_filters.Filter]:
        """Create filters that require special handling (NOT operations, etc.)."""
        
        class NotFilter(config.field_class):
            """Filter that negates the condition."""
            
            def filter(self, qs, value):
                if value is None:
                    return qs
                
                # Build the positive condition first
                if config.operator.value == 'not_exact':
                    lookup = {f"{field_name}": value}
                elif config.operator.value == 'not_in':
                    lookup = {f"{field_name}__in": value}
                else:
                    return qs
                
                # Return the negated queryset
                return qs.exclude(**lookup)
        
        # Create the not filter instance with appropriate parameters
        filter_kwargs = {
            'field_name': field_name,
            'label': label,
            'help_text': help_text
        }
        
        # Add queryset for related fields when using Model filters
        if isinstance(field, (models.ForeignKey, models.OneToOneField, models.ManyToManyField)):
            if cls._filter_requires_queryset(config.field_class):
                filter_kwargs['queryset'] = field.related_model.objects.all()
        
        try:
            return NotFilter(**filter_kwargs)
        except Exception:
            # If special filter creation fails, return None instead of crashing
            return None
    
    @classmethod
    def _generate_range_filters(
        cls, 
        field: models.Field, 
        verbose_name: str,
        include_multiple_ranges: bool = True
    ) -> Dict[str, django_filters.Filter]:
        """Generate range filters for applicable field types."""
        from django.db.models.fields import (
            DateField, DateTimeField, TimeField, IntegerField, 
            FloatField, DecimalField
        )
        
        filters = {}
        field_name = field.name
        
        if isinstance(field, (DateField, DateTimeField)):
            # Date/DateTime range filter
            filters[f"{field_name}__range"] = DateRangeFilter(
                field_name=field_name,
                label=f"{verbose_name.capitalize()} Range",
                help_text=f"Filter {verbose_name} by date range (from,to or JSON format)"
            )
            # Multiple date ranges with logical operators
            if include_multiple_ranges:
                filters[f"{field_name}__multi_range"] = MultipleRangeFilter(
                    field_name=field_name,
                    label=f"{verbose_name.capitalize()} Multiple Ranges",
                    help_text=f"Filter {verbose_name} by multiple date ranges with AND/OR logic"
                )
        
        elif isinstance(field, TimeField):
            # Time range filter
            filters[f"{field_name}__range"] = TimeRangeFilter(
                field_name=field_name,
                label=f"{verbose_name.capitalize()} Range",
                help_text=f"Filter {verbose_name} by time range (from,to or JSON format)"
            )
            # Multiple time ranges
            if include_multiple_ranges:
                filters[f"{field_name}__multi_range"] = MultipleRangeFilter(
                    field_name=field_name,
                    label=f"{verbose_name.capitalize()} Multiple Ranges",
                    help_text=f"Filter {verbose_name} by multiple time ranges with AND/OR logic"
                )
        
        elif isinstance(field, (IntegerField, FloatField, DecimalField)):
            # Numeric range filter
            filters[f"{field_name}__range"] = NumericRangeFilter(
                field_name=field_name,
                label=f"{verbose_name.capitalize()} Range",
                help_text=f"Filter {verbose_name} by numeric range (from,to or JSON format)"
            )
            # Multiple numeric ranges with logical operators
            if include_multiple_ranges:
                filters[f"{field_name}__multi_range"] = MultipleRangeFilter(
                    field_name=field_name,
                    label=f"{verbose_name.capitalize()} Multiple Ranges",
                    help_text=f"Filter {verbose_name} by multiple numeric ranges with AND/OR logic"
                )
        
        return filters
    
    @classmethod
    def get_filter_class_for_model(
        cls, 
        model_class: Type[models.Model], 
        field_names: Optional[List[str]] = None,
        include_logical: bool = True,
        include_ranges: bool = True,
        include_multiple_ranges: bool = True
    ) -> Type['AutoFilterSet']:
        """
        Create a comprehensive FilterSet class for a specific model with all filters.
        
        Args:
            model_class: The model class to create filters for
            field_names: Optional list of field names to generate filters for
            include_logical: Whether to include logical filter
            include_ranges: Whether to include range filters
            include_multiple_ranges: Whether to include multiple range filters
        """
        
        # Generate comprehensive filter fields
        filter_fields = cls.generate_filters(
            model_class, field_names, include_logical, include_ranges, include_multiple_ranges
        )
        
        # Create Meta class  
        meta_attrs = {
            'model': model_class,
            'fields': '__all__',
        }
        
        # Create the FilterSet class
        attrs = {
            'Meta': type('Meta', (), meta_attrs),
            **filter_fields
        }
        
        class_name = f'{model_class.__name__}AutoFilterSet'
        return type(class_name, (cls,), attrs)
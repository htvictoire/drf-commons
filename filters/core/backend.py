"""
Filter backend for automatic filter generation.
"""

from django_filters import rest_framework as django_filters
from .filterset import AutoFilterSet


class AutoFilterBackend(django_filters.DjangoFilterBackend):
    """
    Comprehensive filter backend with operational filters, logical connectors, and range filters.
    
    Usage in views:
        class MyModelViewSet(viewsets.ModelViewSet):
            queryset = MyModel.objects.all()
            filter_backends = [AutoFilterBackend]
            # Optional: limit fields
            filter_fields = ['name', 'status', 'created_at']
            # Optional: disable logical filter
            include_logical_filter = False
            # Optional: disable range filters
            include_range_filters = False
            # Optional: disable multiple range filters
            include_multiple_range_filters = False
    """
    
    def get_filterset_class(self, view, queryset=None):
        """Return the comprehensive filterset class for the view."""
        
        # Check for custom filterset_class
        if hasattr(view, 'filterset_class'):
            return view.filterset_class
        
        # Get configuration from view
        model_class = queryset.model
        field_names = getattr(view, 'filter_fields', None)
        include_logical = getattr(view, 'include_logical_filter', True)
        include_ranges = getattr(view, 'include_range_filters', True)
        include_multiple_ranges = getattr(view, 'include_multiple_range_filters', True)
        
        # Generate comprehensive FilterSet
        return AutoFilterSet.get_filter_class_for_model(
            model_class=model_class,
            field_names=field_names,
            include_logical=include_logical,
            include_ranges=include_ranges,
            include_multiple_ranges=include_multiple_ranges
        )
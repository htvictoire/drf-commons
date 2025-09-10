from django.db import models
from rest_framework.filters import OrderingFilter


class ComputedOrderingFilter(OrderingFilter):
    """
    Extended OrderingFilter that handles computed field ordering.
    
    ViewSets can define computed_ordering_fields as a dict mapping field names 
    to their database lookup paths.
    
    Example:
    class MyViewSet(GenericViewSet):
        computed_ordering_fields = {
            'student': ['registration__student__first_name', 'registration__student__last_name'],
            'academic_class': 'academic_class__name',
            'classes_count': models.Count('classes'),
        }
    """
    
    def get_valid_fields(self, queryset, view, context=None):
        valid_fields = super().get_valid_fields(queryset, view, context)
        
        # Add computed ordering fields
        computed_fields = getattr(view, 'computed_ordering_fields', {})
        if computed_fields:
            # Add each computed field key as a valid ordering field
            for field_name in computed_fields.keys():
                valid_fields.append((field_name, field_name))
        
        return valid_fields
    
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            # Check if we have computed ordering fields defined in the view
            computed_fields = getattr(view, 'computed_ordering_fields', {})
            
            if computed_fields:
                processed_ordering = []
                annotations = {}
                
                for order_field in ordering:
                    # Remove leading minus for reverse ordering check
                    field_name = order_field.lstrip('-')
                    is_reverse = order_field.startswith('-')
                    
                    if field_name in computed_fields:
                        lookup = computed_fields[field_name]
                        
                        # Handle different lookup types
                        if isinstance(lookup, str):
                            # Simple string lookup
                            final_field = f"-{lookup}" if is_reverse else lookup
                            processed_ordering.append(final_field)
                        elif isinstance(lookup, list):
                            # List of fields for compound ordering
                            if is_reverse:
                                order_fields = [f"-{field}" for field in lookup]
                            else:
                                order_fields = lookup
                            processed_ordering.extend(order_fields)
                        elif isinstance(lookup, models.Aggregate):
                            # Annotation case (like Count)
                            annotation_name = f"{field_name}_order"
                            annotations[annotation_name] = lookup
                            final_field = f"-{annotation_name}" if is_reverse else annotation_name
                            processed_ordering.append(final_field)
                    else:
                        # Regular field, keep as is
                        processed_ordering.append(order_field)
                
                # Apply annotations if any
                if annotations:
                    queryset = queryset.annotate(**annotations)
                
                # Apply the processed ordering
                if processed_ordering:
                    return queryset.order_by(*processed_ordering)
        
        # Fall back to default behavior for regular fields
        return super().filter_queryset(request, queryset, view)
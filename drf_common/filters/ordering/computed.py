from rest_framework.filters import OrderingFilter

from .processors import process_ordering


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
        """Extend valid fields to include computed fields."""
        valid_fields = super().get_valid_fields(queryset, view, context)

        computed_fields = getattr(view, "computed_ordering_fields", {})
        if computed_fields:
            for field_name in computed_fields.keys():
                valid_fields.append((field_name, field_name))

        return valid_fields

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            computed_fields = getattr(view, "computed_ordering_fields", {})

            if computed_fields:
                processed_ordering, annotations = process_ordering(
                    ordering, computed_fields
                )

                # Apply annotations if any
                if annotations:
                    queryset = queryset.annotate(**annotations)

                # Apply the processed ordering
                if processed_ordering:
                    return queryset.order_by(*processed_ordering)

        # Fall back to default behavior for regular fields
        return super().filter_queryset(request, queryset, view)

from django.db import models


def parse_order_field(order_field):
    """Parse order field to extract field name and reverse flag."""
    is_reverse = order_field.startswith("-")
    field_name = order_field[1:] if is_reverse else order_field
    return field_name, is_reverse


def process_string_lookup(lookup, is_reverse):
    """Process simple string lookup."""
    return [f"-{lookup}" if is_reverse else lookup]


def process_list_lookup(lookup, is_reverse):
    """Process list of fields for compound ordering."""
    if is_reverse:
        return [f"-{field}" for field in lookup]
    return lookup


def process_aggregate_lookup(lookup, field_name, is_reverse):
    """Process aggregate lookup (like Count) and return annotation info."""
    annotation_name = f"{field_name}_order"
    annotation = {annotation_name: lookup}
    final_field = f"-{annotation_name}" if is_reverse else annotation_name
    return [final_field], annotation


def process_computed_field(field_name, lookup, is_reverse):
    """
    Process a computed field based on its lookup type.

    Returns:
        tuple: (ordering_fields, annotations_dict)
    """
    if isinstance(lookup, str):
        return process_string_lookup(lookup, is_reverse), {}
    elif isinstance(lookup, list):
        return process_list_lookup(lookup, is_reverse), {}
    elif isinstance(lookup, models.Aggregate):
        return process_aggregate_lookup(lookup, field_name, is_reverse)
    else:
        raise ValueError(f"Unsupported lookup type: {type(lookup)}")


def process_ordering(ordering, computed_fields):
    """
    Process ordering list with computed fields.

    Args:
        ordering: List of ordering fields from request
        computed_fields: Dict of computed field definitions

    Returns:
        tuple: (processed_ordering, annotations)
    """
    processed_ordering = []
    annotations = {}

    for order_field in ordering:
        field_name, is_reverse = parse_order_field(order_field)

        if field_name in computed_fields:
            lookup = computed_fields[field_name]
            order_fields, field_annotations = process_computed_field(
                field_name, lookup, is_reverse
            )
            processed_ordering.extend(order_fields)
            annotations.update(field_annotations)
        else:
            # Regular field, keep as is
            processed_ordering.append(order_field)

    return processed_ordering, annotations

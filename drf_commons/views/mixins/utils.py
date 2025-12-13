"""
Utility functions for mixins.
"""


def get_model_name(viewset_instance):
    """
    Get the model name for messages from a viewset instance.

    Args:
        viewset_instance: ViewSet instance that may have queryset or model attributes

    Returns:
        str: Model verbose name plural (title case), model name, or "Objects" as fallback
    """
    if hasattr(viewset_instance, "queryset") and viewset_instance.queryset is not None:
        model_meta = viewset_instance.queryset.model._meta
        name = (
            model_meta.verbose_name_plural or viewset_instance.queryset.model.__name__
        )
        return name.title()
    elif hasattr(viewset_instance, "model") and viewset_instance.model is not None:
        model_meta = viewset_instance.model._meta
        name = model_meta.verbose_name_plural or viewset_instance.model.__name__
        return name.title()
    return "Objects"


def get_operation_message(
    viewset_instance, action_type, count=None, operation_prefix=""
):
    """
    Generate operation message with model name.

    Args:
        viewset_instance: ViewSet instance
        action_type: Type of action (e.g., "created", "updated", "deleted")
        count: Number of objects affected (optional)
        operation_prefix: Prefix for the operation (e.g., "Bulk", "")

    Returns:
        str: Formatted operation message
    """
    model_name = get_model_name(viewset_instance)
    prefix = f"{operation_prefix} " if operation_prefix else ""

    if count is not None:
        return f"{prefix}{action_type.title()} {count} {model_name} successfully."
    return f"{prefix}{action_type.title()} operation completed successfully."

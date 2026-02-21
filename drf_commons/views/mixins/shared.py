"""
Shared view mixins used by CRUD and bulk endpoints.
"""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from drf_commons.serializers.fields.mixins import ConfigurableRelatedFieldMixin


def _collect_unsupported_bulk_serializer_fields(serializer):
    """Return writable nested/custom fields not supported in direct bulk mode."""
    child = getattr(serializer, "child", serializer)
    fields = getattr(child, "fields", {})
    unsupported_fields = []

    for field_name, field in fields.items():
        if getattr(field, "read_only", False):
            continue
        if isinstance(field, ConfigurableRelatedFieldMixin):
            unsupported_fields.append(field_name)
            continue
        if isinstance(field, serializers.BaseSerializer):
            unsupported_fields.append(field_name)

    return sorted(set(unsupported_fields))


class BulkDirectSerializerContractMixin:
    """
    Validate that direct bulk create/update payloads do not use nested/custom fields.
    """

    bulk_direct_serializers_only = True

    def _validate_bulk_direct_serializer_contract(self, serializer, operation):
        if not self.bulk_direct_serializers_only:
            return

        unsupported_fields = _collect_unsupported_bulk_serializer_fields(serializer)
        if not unsupported_fields:
            return

        raise ValidationError(
            {
                "non_field_errors": [
                    (
                        f"Bulk {operation} supports direct serializers only. "
                        f"Unsupported fields: {', '.join(unsupported_fields)}. "
                        "Use non-bulk endpoints for nested/custom serializer behavior."
                    )
                ]
            }
        )

"""
Base serializer classes for bulk operations.

This module provides optimized serializers for bulk create, update, and delete operations.
These serializers handle multiple instances efficiently with single database calls.
"""

from django.db import transaction
from rest_framework import serializers

from .fields.mixins import ConfigurableRelatedFieldMixin, DeferredRelatedOperation


class BulkUpdateListSerializer(serializers.ListSerializer):
    """
    Custom ListSerializer that handles bulk updates efficiently.

    Contract: this serializer performs direct attribute assignment + bulk_update and
    intentionally rejects deferred nested relation writes.
    """

    @staticmethod
    def _contains_deferred_related_operation(value):
        """Return True when value contains deferred nested relation writes."""
        if isinstance(value, DeferredRelatedOperation):
            return True
        if isinstance(value, list):
            return any(
                BulkUpdateListSerializer._contains_deferred_related_operation(item)
                for item in value
            )
        if isinstance(value, tuple):
            return any(
                BulkUpdateListSerializer._contains_deferred_related_operation(item)
                for item in value
            )
        return False

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update multiple instances efficiently using bulk operations.
        """
        instances = list(instance)
        if len(instances) != len(validated_data):
            raise serializers.ValidationError(
                "Bulk update payload/instance count mismatch. "
                "Each payload row must resolve to exactly one instance."
            )

        # Match instances with validated data by position
        instances_to_update = []
        update_fields = set()

        for idx, (inst, item_data) in enumerate(zip(instances, validated_data)):
            for attr, value in item_data.items():
                if self._contains_deferred_related_operation(value):
                    raise serializers.ValidationError(
                        {
                            idx: (
                                f"Field '{attr}' uses nested/custom deferred relation "
                                "writes which are not supported in bulk update."
                            )
                        }
                    )
                setattr(inst, attr, value)
                update_fields.add(attr)
            instances_to_update.append(inst)

        # Perform bulk update
        if instances_to_update and update_fields:
            # Use the model class from the first instance
            model_class = instances_to_update[0].__class__
            model_class.objects.bulk_update(instances_to_update, list(update_fields))

        return instances_to_update


class BaseModelSerializer(serializers.ModelSerializer):
    """
    ModelSerializer that supports efficient bulk operations.

    This serializer provides optimized bulk operations that minimize database calls.
    """

    class Meta:
        list_serializer_class = BulkUpdateListSerializer

    def _get_configurable_related_field(self, data_key):
        field = self.fields.get(data_key)
        if isinstance(field, ConfigurableRelatedFieldMixin):
            return field

        for field_name, candidate in self.fields.items():
            if not isinstance(candidate, ConfigurableRelatedFieldMixin):
                continue
            source = field_name if candidate.source in (None, "*") else candidate.source
            if source == data_key:
                return candidate
        return None

    def _extract_root_first_related_values(self, validated_data):
        root_first_values = {}
        for data_key in list(validated_data.keys()):
            field = self._get_configurable_related_field(data_key)
            if not field:
                continue
            if field.get_relation_write_order() == "root_first":
                root_first_values[data_key] = validated_data.pop(data_key)
        return root_first_values

    def _resolve_dependency_first_related_values(self, validated_data):
        for data_key, value in list(validated_data.items()):
            field = self._get_configurable_related_field(data_key)
            if not field:
                continue
            if field.get_relation_write_order() != "dependency_first":
                continue
            if field.contains_deferred_related(value):
                validated_data[data_key] = field.resolve_related_value(value)

    def _apply_root_first_related_values(self, instance, root_first_values):
        for data_key, value in root_first_values.items():
            field = self._get_configurable_related_field(data_key)
            if not field:
                continue
            resolved = field.resolve_related_value(value, parent_instance=instance)
            field.apply_root_first_relation(instance, resolved)

    def create(self, validated_data):
        root_first_values = self._extract_root_first_related_values(validated_data)
        self._resolve_dependency_first_related_values(validated_data)
        instance = super().create(validated_data)
        self._apply_root_first_related_values(instance, root_first_values)
        return instance

    def update(self, instance, validated_data):
        root_first_values = self._extract_root_first_related_values(validated_data)
        self._resolve_dependency_first_related_values(validated_data)
        instance = super().update(instance, validated_data)
        self._apply_root_first_related_values(instance, root_first_values)
        return instance

    @transaction.atomic
    def save(self, **kwargs):
        """
        Wrap save operations in database transaction for data consistency.
        """
        return super().save(**kwargs)

"""
Base serializer classes for bulk operations.

This module provides optimized serializers for bulk create, update, and delete operations.
These serializers handle multiple instances efficiently with single database calls.
"""

from django.db import transaction
from rest_framework import serializers


class BulkUpdateListSerializer(serializers.ListSerializer):
    """
    Custom ListSerializer that handles bulk updates efficiently.
    """

    @transaction.atomic
    def update(self, instance, validated_data):
        """
        Update multiple instances efficiently using bulk operations.
        """
        # Match instances with validated data by position
        instances_to_update = []
        update_fields = set()

        for inst, item_data in zip(instance, validated_data):
            for attr, value in item_data.items():
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

    @transaction.atomic
    def save(self, **kwargs):
        """
        Wrap save operations in database transaction for data consistency.
        """
        return super().save(**kwargs)
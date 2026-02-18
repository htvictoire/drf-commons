"""Deferred write operation primitives."""

from dataclasses import dataclass

from rest_framework import serializers


@dataclass
class DeferredRelatedOperation:
    """Represents a nested relation write deferred until serializer save."""

    field: "ConfigurableRelatedFieldMixin"
    serializer: serializers.Serializer

    def resolve(self, parent_instance=None):
        return self.field._save_deferred_serializer(
            self.serializer, parent_instance=parent_instance
        )

"""Deferred write operation primitives."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

from rest_framework import serializers

if TYPE_CHECKING:
    from .base import ConfigurableRelatedFieldMixin


@dataclass
class DeferredRelatedOperation:
    """Represents a nested relation write deferred until serializer save."""

    field: "ConfigurableRelatedFieldMixin"
    serializer: serializers.Serializer

    def resolve(self, parent_instance=None):
        return self.field._save_deferred_serializer(
            self.serializer, parent_instance=parent_instance
        )

"""
Common field testing utilities and mock classes.
"""

from rest_framework import serializers

from drf_commons.serializers.fields.mixins import ConfigurableRelatedFieldMixin
from .base import UserSerializerForTesting


class MockField(ConfigurableRelatedFieldMixin, serializers.RelatedField):
    """Basic mock field for testing ConfigurableRelatedFieldMixin."""

    pass


class MockFieldWithDefaults(ConfigurableRelatedFieldMixin, serializers.RelatedField):
    """Mock field with safe defaults that don't require serializer_class."""

    def __init__(self, **kwargs):
        kwargs.setdefault("output_format", "id")
        kwargs.setdefault("input_formats", ["id"])
        super().__init__(**kwargs)


class MockFieldWithSerializer(ConfigurableRelatedFieldMixin, serializers.RelatedField):
    """Mock field that includes a serializer by default."""

    def __init__(self, **kwargs):
        kwargs.setdefault("serializer_class", UserSerializerForTesting)
        super().__init__(**kwargs)


def create_mock_field(queryset, **kwargs):
    """Factory function to create a mock field with defaults."""
    input_formats = kwargs.get('input_formats', ['id'])
    output_format = kwargs.get('output_format', 'id')

    if ('nested' in input_formats or output_format == 'serialized') and 'serializer_class' not in kwargs:
        kwargs['serializer_class'] = UserSerializerForTesting

    return MockFieldWithDefaults(queryset=queryset, **kwargs)


def create_serialized_mock_field(queryset, **kwargs):
    """Factory function to create a mock field that uses serialized output."""
    return MockFieldWithSerializer(queryset=queryset, **kwargs)

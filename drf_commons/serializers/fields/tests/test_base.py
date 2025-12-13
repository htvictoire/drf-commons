"""
Tests for base configurable field classes.

Tests core functionality of ConfigurableRelatedField, ConfigurableManyToManyField,
ReadOnlyRelatedField, and WriteOnlyRelatedField.
"""

from django.contrib.auth import get_user_model

from rest_framework import serializers

from drf_commons.common_tests.base_cases import SerializerTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.common_tests.serializers import UserSerializerForTesting

from ..base import (
    ConfigurableManyToManyField,
    ConfigurableRelatedField,
    ReadOnlyRelatedField,
    WriteOnlyRelatedField,
)

User = get_user_model()


class ConfigurableRelatedFieldTests(SerializerTestCase):
    """Tests for ConfigurableRelatedField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_initialization(self):
        """Test field initializes correctly."""
        field = ConfigurableRelatedField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting
        )
        self.assertIsInstance(field, ConfigurableRelatedField)

    def test_field_with_serializer_class(self):
        """Test field initialization with serializer_class parameter."""
        field = ConfigurableRelatedField(
            queryset=self.queryset, serializer_class=UserSerializerForTesting
        )
        self.assertEqual(field.serializer_class, UserSerializerForTesting)


class ConfigurableManyToManyFieldTests(SerializerTestCase):
    """Tests for ConfigurableManyToManyField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_initializes_with_many_true(self):
        """Test field initializes with many=True."""
        field = ConfigurableManyToManyField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting
        )
        result = field.to_representation([self.user])
        self.assertIsInstance(result, list)

    def test_empty_representation_returns_empty_list(self):
        """Test empty values return empty list."""
        field = ConfigurableManyToManyField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting
        )
        result = field.to_representation(None)
        self.assertEqual(result, [])


class ReadOnlyRelatedFieldTests(SerializerTestCase):
    """Tests for ReadOnlyRelatedField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_field_initializes_as_read_only(self):
        """Test field initializes with read_only=True."""
        field = ReadOnlyRelatedField(serializer_class=UserSerializerForTesting)
        self.assertTrue(field.read_only)

    def test_field_rejects_input_data(self):
        """Test field rejects input data."""
        field = ReadOnlyRelatedField(serializer_class=UserSerializerForTesting)
        with self.assertRaises(serializers.ValidationError):
            field.to_internal_value({"id": 1})


class WriteOnlyRelatedFieldTests(SerializerTestCase):
    """Tests for WriteOnlyRelatedField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_initializes_as_write_only(self):
        """Test field initializes with write_only=True."""
        field = WriteOnlyRelatedField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting
        )
        self.assertTrue(field.write_only)

    def test_field_returns_none_for_representation(self):
        """Test field returns None for representation."""
        field = WriteOnlyRelatedField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting
        )
        result = field.to_representation(self.user)
        self.assertIsNone(result)

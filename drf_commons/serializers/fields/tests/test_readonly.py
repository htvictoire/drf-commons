"""
Tests for read-only related field types.

Tests pre-configured read-only field types like
ReadOnlyIdField, ReadOnlyStrField, etc.
"""

from django.contrib.auth import get_user_model

from rest_framework import serializers

from drf_commons.common_tests.base_cases import SerializerTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.common_tests.serializers import UserSerializerForTesting

from ..readonly import (
    ReadOnlyCustomField,
    ReadOnlyDataField,
    ReadOnlyIdField,
    ReadOnlyStrField,
)

User = get_user_model()


class ReadOnlyIdFieldTests(SerializerTestCase):
    """Tests for ReadOnlyIdField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = ReadOnlyIdField(input_formats=["id"])
        self.assertEqual(field.output_format, "id")
        self.assertTrue(field.read_only)

    def test_field_rejects_input(self):
        """Test field rejects input data."""
        field = ReadOnlyIdField(input_formats=["id"])
        with self.assertRaises(serializers.ValidationError):
            field.to_internal_value({"id": 1})


class ReadOnlyStrFieldTests(SerializerTestCase):
    """Tests for ReadOnlyStrField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = ReadOnlyStrField(input_formats=["id"])
        self.assertEqual(field.output_format, "str")
        self.assertTrue(field.read_only)

    def test_field_rejects_input(self):
        """Test field rejects input data."""
        field = ReadOnlyStrField(input_formats=["id"])
        with self.assertRaises(serializers.ValidationError):
            field.to_internal_value({"id": 1})


class ReadOnlyDataFieldTests(SerializerTestCase):
    """Tests for ReadOnlyDataField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = ReadOnlyDataField(serializer_class=UserSerializerForTesting, input_formats=["id"])
        self.assertEqual(field.output_format, "serialized")
        self.assertTrue(field.read_only)

    def test_field_rejects_input(self):
        """Test field rejects input data."""
        field = ReadOnlyDataField(serializer_class=UserSerializerForTesting, input_formats=["id"])
        with self.assertRaises(serializers.ValidationError):
            field.to_internal_value({"id": 1})


class ReadOnlyCustomFieldTests(SerializerTestCase):
    """Tests for ReadOnlyCustomField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        def custom_callable(obj, ctx):
            return f"User: {obj.username}"
        field = ReadOnlyCustomField(custom_output_callable=custom_callable, input_formats=["id"])
        self.assertEqual(field.output_format, "custom")
        self.assertEqual(field.custom_output_callable, custom_callable)
        self.assertTrue(field.read_only)

    def test_field_rejects_input(self):
        """Test field rejects input data."""
        def custom_callable(obj, ctx):
            return f"User: {obj.username}"
        field = ReadOnlyCustomField(custom_output_callable=custom_callable, input_formats=["id"])
        with self.assertRaises(serializers.ValidationError):
            field.to_internal_value({"id": 1})

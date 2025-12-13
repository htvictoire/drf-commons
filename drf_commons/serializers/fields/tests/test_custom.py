"""
Tests for custom and flexible related field types.

Tests custom field types like FlexibleField and CustomOutputField
that provide advanced configuration options.
"""

from django.contrib.auth import get_user_model

from rest_framework import serializers

from drf_commons.common_tests.base_cases import SerializerTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.common_tests.serializers import UserSerializerForTesting

from ..custom import (
    CustomOutputField,
    FlexibleField,
)

User = get_user_model()




class FlexibleFieldTests(SerializerTestCase):
    """Tests for FlexibleField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = FlexibleField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting
        )
        self.assertEqual(field.input_formats, ["id", "nested", "slug"])
        self.assertEqual(field.output_format, "serialized")

    def test_field_accepts_multiple_input_formats(self):
        """Test field accepts multiple input formats."""
        field = FlexibleField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting
        )
        self.assertIn("id", field.input_formats)
        self.assertIn("nested", field.input_formats)
        self.assertIn("slug", field.input_formats)


class CustomOutputFieldTests(SerializerTestCase):
    """Tests for CustomOutputField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        def custom_callable(obj, ctx):
            return f"User: {obj.username}"
        field = CustomOutputField(
            queryset=self.queryset,
            custom_output_callable=custom_callable,
            serializer_class=UserSerializerForTesting
        )
        self.assertEqual(field.input_formats, ["id", "nested"])
        self.assertEqual(field.output_format, "custom")
        self.assertEqual(field.custom_output_callable, custom_callable)

    def test_field_requires_custom_callable(self):
        """Test field requires custom_output_callable parameter."""
        with self.assertRaises(TypeError):
            CustomOutputField(queryset=self.queryset)

    def test_custom_callable_parameter_set(self):
        """Test custom_output_callable parameter is set correctly."""

        def custom_formatter(obj, context):
            return f"Custom: {obj.username}"

        field = CustomOutputField(
            queryset=self.queryset,
            custom_output_callable=custom_formatter,
            serializer_class=UserSerializerForTesting
        )
        self.assertEqual(field.custom_output_callable, custom_formatter)

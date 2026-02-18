"""
Tests for configurable related field mixins.

Tests core mixin functionality that provides the foundation
for all configurable related field functionality.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.conf import settings as django_settings

from rest_framework import serializers

from drf_commons.common_tests.base_cases import SerializerTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.common_tests.serializers import (
    UserSerializerForTesting,
    MockField,
    MockFieldWithDefaults,
    MockFieldWithSerializer,
    create_mock_field,
    create_serialized_mock_field,
)

User = get_user_model()


class ConfigurableRelatedFieldMixinTests(SerializerTestCase):
    """Tests for ConfigurableRelatedFieldMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_mixin_initialization_with_defaults(self):
        """Test mixin initializes with default configuration."""
        field = create_serialized_mock_field(queryset=self.queryset)
        self.assertEqual(field.input_formats, ["id", "nested"])
        self.assertEqual(field.output_format, "serialized")
        self.assertEqual(field.lookup_field, "pk")
        self.assertTrue(field.create_if_nested)
        self.assertFalse(field.update_if_exists)
        self.assertIsNone(field.custom_output_callable)

    def test_mixin_initialization_with_custom_values(self):
        """Test mixin initializes with custom configuration."""
        def custom_callable(obj, ctx):
            return f"User: {obj.username}"
        field = MockField(
            queryset=self.queryset,
            input_formats=["id", "slug"],
            output_format="custom",
            lookup_field="id",
            create_if_nested=False,
            update_if_exists=True,
            custom_output_callable=custom_callable,
        )
        self.assertEqual(field.input_formats, ["id", "slug"])
        self.assertEqual(field.output_format, "custom")
        self.assertEqual(field.lookup_field, "id")
        self.assertFalse(field.create_if_nested)
        self.assertTrue(field.update_if_exists)
        self.assertEqual(field.custom_output_callable, custom_callable)

    def test_configuration_validation_invalid_input_formats(self):
        """Test validation rejects invalid input formats."""
        with self.assertRaises(ValueError) as cm:
            MockField(
                queryset=self.queryset,
                input_formats=["invalid"],
                output_format="id"
            )
        self.assertIn("Invalid input_formats", str(cm.exception))

    def test_configuration_validation_invalid_output_format(self):
        """Test validation rejects invalid output formats."""
        with self.assertRaises(ValueError) as cm:
            MockField(
                queryset=self.queryset,
                output_format="invalid",
                input_formats=["id"]
            )
        self.assertIn("Invalid output_format", str(cm.exception))

    def test_configuration_validation_serialized_without_serializer_class(self):
        """Test validation requires serializer_class for serialized output."""
        with self.assertRaises(ValueError) as cm:
            MockField(
                queryset=self.queryset,
                output_format="serialized",
                serializer_class=None,
            )
        self.assertIn("serializer_class is required", str(cm.exception))

    def test_configuration_validation_custom_without_callable(self):
        """Test validation requires custom_output_callable for custom output."""
        with self.assertRaises(ValueError) as cm:
            MockField(
                queryset=self.queryset,
                output_format="custom",
                custom_output_callable=None,
                input_formats=["id"]
            )
        self.assertIn("custom_output_callable is required", str(cm.exception))

    def test_configuration_validation_nested_without_serializer_class(self):
        """Test validation requires serializer_class for nested input."""
        with self.assertRaises(ValueError) as cm:
            MockField(
                queryset=self.queryset,
                input_formats=["nested"],
                output_format="id"
            )
        self.assertIn("serializer_class is required", str(cm.exception))

    def test_to_representation_with_none_value(self):
        """Test representation returns None for None value."""
        field = create_mock_field(queryset=self.queryset)
        result = field.to_representation(None)
        self.assertIsNone(result)

    def test_to_representation_with_id_format(self):
        """Test representation returns ID for id format."""
        field = create_mock_field(queryset=self.queryset)
        field.lookup_field = "pk"
        result = field.to_representation(self.user)
        self.assertEqual(result, self.user.pk)

    def test_to_representation_with_str_format(self):
        """Test representation returns string for str format."""
        field = create_mock_field(
            queryset=self.queryset,
            output_format="str"
        )
        result = field.to_representation(self.user)
        self.assertEqual(result, str(self.user))

    def test_to_representation_with_custom_format(self):
        """Test representation uses custom callable for custom format."""
        def custom_callable(obj, ctx):
            return f"User: {obj.username}"
        field = MockField(
            queryset=self.queryset,
            output_format="custom",
            custom_output_callable=custom_callable,
            input_formats=["id"]
        )
        result = field.to_representation(self.user)
        self.assertEqual(result, f"User: {self.user.username}")

    def test_to_internal_value_with_null_and_allow_null_true(self):
        """Test internal value handles null when allow_null is True."""
        field = create_mock_field(queryset=self.queryset, allow_null=True)
        result = field.to_internal_value(None)
        self.assertIsNone(result)

    def test_to_internal_value_with_null_and_allow_null_false(self):
        """Test internal value rejects null when allow_null is False."""
        field = create_mock_field(queryset=self.queryset, allow_null=False)
        field.error_messages = {"null": "This field may not be null."}
        with self.assertRaises(Exception):
            field.to_internal_value(None)

    def test_handle_id_input_with_valid_id(self):
        """Test ID input handling with valid ID."""
        field = create_mock_field(queryset=self.queryset, input_formats=["id"])
        result = field._handle_id_input(self.user.pk)
        self.assertEqual(result, self.user)

    def test_handle_id_input_with_invalid_id(self):
        """Test ID input handling with non-existent ID."""
        field = create_mock_field(queryset=self.queryset, input_formats=["id"])
        field.error_messages = {"does_not_exist": "Object does not exist."}
        with self.assertRaises(Exception):
            field._handle_id_input(99999)

    def test_handle_slug_input_with_username(self):
        """Test slug input handling using username as slug field."""
        user_with_name = UserFactory(username="test-slug")
        field = create_mock_field(queryset=self.queryset, input_formats=["slug"])
        result = field.queryset.get(username="test-slug")
        self.assertEqual(result, user_with_name)

    def test_configuration_accepts_valid_input_formats(self):
        """Test configuration accepts all valid input formats."""
        valid_formats = ["id", "nested", "slug", "object"]
        field = create_mock_field(
            queryset=self.queryset, input_formats=valid_formats
        )
        self.assertEqual(field.input_formats, valid_formats)

    def test_configuration_accepts_valid_output_formats(self):
        """Test configuration accepts all valid output formats."""
        valid_formats = ["id", "str", "serialized", "custom"]
        for fmt in valid_formats:
            if fmt == "custom":
                field = create_mock_field(
                    queryset=self.queryset,
                    output_format=fmt,
                    custom_output_callable=lambda x, y: str(x)
                )
            elif fmt == "serialized":

                class TestSerializer(serializers.ModelSerializer):
                    class Meta:
                        model = User
                        fields = ["id"]

                field = MockField(
                    queryset=self.queryset,
                    output_format=fmt,
                    serializer_class=TestSerializer,
                )
            else:
                field = create_mock_field(queryset=self.queryset, output_format=fmt)
            self.assertEqual(field.output_format, fmt)

    def test_to_internal_value_resolves_slug_when_id_and_slug_enabled(self):
        """Non-numeric strings should resolve through slug lookup when enabled."""
        group = Group.objects.create(name="ops-team")
        field = create_mock_field(
            queryset=Group.objects.all(),
            input_formats=["id", "slug"],
        )

        result = field.to_internal_value("ops-team")

        self.assertEqual(result, group)

    def test_to_internal_value_numeric_string_prefers_id_lookup(self):
        """Numeric strings should resolve through ID lookup when available."""
        group = Group.objects.create(name="group-1")
        field = create_mock_field(
            queryset=Group.objects.all(),
            input_formats=["id", "slug"],
        )

        result = field.to_internal_value(str(group.pk))

        self.assertEqual(result, group)

    def test_to_internal_value_numeric_string_falls_back_to_slug(self):
        """If numeric ID lookup fails, numeric slug-like names still resolve."""
        group = Group.objects.create(name="404")
        field = create_mock_field(
            queryset=Group.objects.all(),
            input_formats=["id", "slug"],
        )
        field.error_messages = {
            "does_not_exist": "Object does not exist.",
            "incorrect_type": "Incorrect type.",
        }

        result = field.to_internal_value("404")

        self.assertEqual(result, group)

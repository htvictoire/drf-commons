"""
Tests for many-to-many related field types.

Tests pre-configured many-to-many field types like
ManyIdToDataField, ManyDataToIdField, etc.
"""

from django.contrib.auth import get_user_model

from drf_commons.common_tests.base_cases import SerializerTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.common_tests.serializers import UserSerializerForTesting

from ..many import (
    ManyDataToIdField,
    ManyFlexibleField,
    ManyIdOnlyField,
    ManyIdToDataField,
    ManyStrOnlyField,
    ManyStrToDataField,
)

User = get_user_model()


class ManyIdToDataFieldTests(SerializerTestCase):
    """Tests for ManyIdToDataField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = ManyIdToDataField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting
        )
        self.assertEqual(field.input_formats, ["id"])
        self.assertEqual(field.output_format, "serialized")
        # Test many behavior by checking empty representation
        self.assertEqual(field.to_representation(None), [])


class ManyDataToIdFieldTests(SerializerTestCase):
    """Tests for ManyDataToIdField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = ManyDataToIdField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting
        )
        self.assertEqual(field.input_formats, ["nested", "id"])
        self.assertEqual(field.output_format, "id")
        # Test many behavior by checking empty representation
        self.assertEqual(field.to_representation(None), [])


class ManyStrToDataFieldTests(SerializerTestCase):
    """Tests for ManyStrToDataField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = ManyStrToDataField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting
        )
        self.assertEqual(field.input_formats, ["slug"])
        self.assertEqual(field.output_format, "serialized")
        # Test many behavior by checking empty representation
        self.assertEqual(field.to_representation(None), [])


class ManyIdOnlyFieldTests(SerializerTestCase):
    """Tests for ManyIdOnlyField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = ManyIdOnlyField(queryset=self.queryset)
        self.assertEqual(field.input_formats, ["id"])
        self.assertEqual(field.output_format, "id")
        # Test many behavior by checking empty representation
        self.assertEqual(field.to_representation(None), [])


class ManyStrOnlyFieldTests(SerializerTestCase):
    """Tests for ManyStrOnlyField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = ManyStrOnlyField(queryset=self.queryset)
        self.assertEqual(field.input_formats, ["slug"])
        self.assertEqual(field.output_format, "str")
        # Test many behavior by checking empty representation
        self.assertEqual(field.to_representation(None), [])


class ManyFlexibleFieldTests(SerializerTestCase):
    """Tests for ManyFlexibleField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = ManyFlexibleField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting
        )
        self.assertEqual(field.input_formats, ["id", "nested", "slug"])
        self.assertEqual(field.output_format, "serialized")
        # Test many behavior by checking empty representation
        self.assertEqual(field.to_representation(None), [])

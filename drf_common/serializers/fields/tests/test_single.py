"""
Tests for single related field types.

Tests pre-configured single related field types like
IdToDataField, DataToIdField, etc.
"""

from django.contrib.auth import get_user_model

from drf_common.common_tests.base_cases import SerializerTestCase
from drf_common.common_tests.factories import UserFactory
from drf_common.common_tests.serializers import UserSerializerForTesting

from ..single import (
    DataToDataField,
    DataToIdField,
    DataToStrField,
    IdOnlyField,
    IdToDataField,
    IdToStrField,
    StrOnlyField,
    StrToDataField,
)

User = get_user_model()


class IdToDataFieldTests(SerializerTestCase):
    """Tests for IdToDataField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = IdToDataField(queryset=self.queryset, serializer_class=UserSerializerForTesting)
        self.assertEqual(field.input_formats, ["id"])
        self.assertEqual(field.output_format, "serialized")


class IdToStrFieldTests(SerializerTestCase):
    """Tests for IdToStrField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = IdToStrField(queryset=self.queryset)
        self.assertEqual(field.input_formats, ["id"])
        self.assertEqual(field.output_format, "str")


class DataToIdFieldTests(SerializerTestCase):
    """Tests for DataToIdField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = DataToIdField(queryset=self.queryset, serializer_class=UserSerializerForTesting)
        self.assertEqual(field.input_formats, ["nested", "id"])
        self.assertEqual(field.output_format, "id")


class DataToStrFieldTests(SerializerTestCase):
    """Tests for DataToStrField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = DataToStrField(queryset=self.queryset, serializer_class=UserSerializerForTesting)
        self.assertEqual(field.input_formats, ["nested", "id"])
        self.assertEqual(field.output_format, "str")


class DataToDataFieldTests(SerializerTestCase):
    """Tests for DataToDataField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = DataToDataField(queryset=self.queryset, serializer_class=UserSerializerForTesting)
        self.assertEqual(field.input_formats, ["nested"])
        self.assertEqual(field.output_format, "serialized")


class StrToDataFieldTests(SerializerTestCase):
    """Tests for StrToDataField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = StrToDataField(queryset=self.queryset, serializer_class=UserSerializerForTesting)
        self.assertEqual(field.input_formats, ["slug"])
        self.assertEqual(field.output_format, "serialized")


class IdOnlyFieldTests(SerializerTestCase):
    """Tests for IdOnlyField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = IdOnlyField(queryset=self.queryset)
        self.assertEqual(field.input_formats, ["id"])
        self.assertEqual(field.output_format, "id")


class StrOnlyFieldTests(SerializerTestCase):
    """Tests for StrOnlyField."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.queryset = User.objects.all()

    def test_field_configuration(self):
        """Test field initializes with correct configuration."""
        field = StrOnlyField(queryset=self.queryset)
        self.assertEqual(field.input_formats, ["slug"])
        self.assertEqual(field.output_format, "str")

"""
Tests for single related field types.

Tests pre-configured single related field types like
IdToDataField, DataToIdField, etc.
"""

from django.contrib.auth import get_user_model

from drf_commons.common_tests.base_cases import SerializerTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.common_tests.serializers import UserSerializerForTesting

from drf_commons.serializers.fields.single import (
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

    def test_relation_write_is_forwarded(self):
        """relation_write kwarg is stored on the field when provided."""
        rw = {"relation_kind": "fk"}
        field = IdToDataField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting,
            relation_write=rw,
        )
        self.assertEqual(field.relation_write, rw)


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

    def test_relation_write_is_forwarded(self):
        rw = {"relation_kind": "fk"}
        field = IdToStrField(queryset=self.queryset, relation_write=rw)
        self.assertEqual(field.relation_write, rw)


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

    def test_relation_write_is_forwarded(self):
        rw = {"write_order": "dependency_first"}
        field = DataToIdField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting,
            relation_write=rw,
        )
        self.assertEqual(field.relation_write, rw)


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

    def test_relation_write_is_forwarded(self):
        rw = {"sync_mode": "replace"}
        field = DataToStrField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting,
            relation_write=rw,
        )
        self.assertEqual(field.relation_write, rw)


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

    def test_relation_write_is_forwarded(self):
        rw = {"relation_kind": "reverse_fk", "child_link_field": "user"}
        field = DataToDataField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting,
            relation_write=rw,
        )
        self.assertEqual(field.relation_write, rw)


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

    def test_relation_write_is_forwarded(self):
        rw = {"relation_kind": "m2m", "sync_mode": "sync"}
        field = StrToDataField(
            queryset=self.queryset,
            serializer_class=UserSerializerForTesting,
            relation_write=rw,
        )
        self.assertEqual(field.relation_write, rw)


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

    def test_relation_write_is_forwarded(self):
        rw = {"write_order": "root_first"}
        field = IdOnlyField(queryset=self.queryset, relation_write=rw)
        self.assertEqual(field.relation_write, rw)


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

    def test_relation_write_is_forwarded(self):
        rw = {"relation_kind": "fk"}
        field = StrOnlyField(queryset=self.queryset, relation_write=rw)
        self.assertEqual(field.relation_write, rw)

"""
Tests for shared view mixin utilities.
"""

from unittest.mock import MagicMock

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from drf_commons.common_tests.base_cases import ViewTestCase
from drf_commons.serializers.fields.mixins import ConfigurableRelatedFieldMixin
from drf_commons.views.mixins.shared import (
    BulkDirectSerializerContractMixin,
    _collect_unsupported_bulk_serializer_fields,
)


def _make_serializer(fields_dict):
    """Build a mock serializer with the given field instances."""
    mock = MagicMock(spec=serializers.Serializer)
    mock.child = mock
    mock.fields = fields_dict
    return mock


class CollectUnsupportedBulkSerializerFieldsTests(ViewTestCase):
    """Tests for _collect_unsupported_bulk_serializer_fields()."""

    def test_plain_field_is_not_flagged(self):
        serializer = _make_serializer({"name": serializers.CharField()})
        result = _collect_unsupported_bulk_serializer_fields(serializer)
        self.assertEqual(result, [])

    def test_read_only_field_is_not_flagged(self):
        field = serializers.CharField(read_only=True)
        serializer = _make_serializer({"id": field})
        result = _collect_unsupported_bulk_serializer_fields(serializer)
        self.assertEqual(result, [])

    def test_configurable_related_field_is_flagged(self):
        field = MagicMock(spec=ConfigurableRelatedFieldMixin)
        field.read_only = False
        serializer = _make_serializer({"owner": field})
        result = _collect_unsupported_bulk_serializer_fields(serializer)
        self.assertIn("owner", result)

    def test_nested_serializer_field_is_flagged(self):
        nested = serializers.Serializer()
        serializer = _make_serializer({"address": nested})
        result = _collect_unsupported_bulk_serializer_fields(serializer)
        self.assertIn("address", result)


class BulkDirectSerializerContractMixinTests(ViewTestCase):
    """Tests for BulkDirectSerializerContractMixin."""

    def test_validation_passes_when_no_unsupported_fields(self):
        mixin = BulkDirectSerializerContractMixin()
        serializer = _make_serializer({"name": serializers.CharField()})
        mixin._validate_bulk_direct_serializer_contract(serializer, "create")

    def test_validation_skipped_when_flag_disabled(self):
        mixin = BulkDirectSerializerContractMixin()
        mixin.bulk_direct_serializers_only = False
        field = MagicMock(spec=ConfigurableRelatedFieldMixin)
        field.read_only = False
        serializer = _make_serializer({"owner": field})
        # Should not raise even with unsupported fields
        mixin._validate_bulk_direct_serializer_contract(serializer, "create")

    def test_validation_raises_for_unsupported_fields(self):
        mixin = BulkDirectSerializerContractMixin()
        nested = serializers.Serializer()
        serializer = _make_serializer({"address": nested})
        with self.assertRaises(ValidationError) as ctx:
            mixin._validate_bulk_direct_serializer_contract(serializer, "create")
        self.assertIn("address", str(ctx.exception.detail))

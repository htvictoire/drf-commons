"""
Tests for base serializers.
"""

from datetime import datetime, timezone as dt_timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from rest_framework import serializers

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.serializers.base import BulkUpdateListSerializer


class _MetaProxy:
    def __init__(self, field_names):
        self._field_names = set(field_names)

    def get_field(self, field_name):
        if field_name not in self._field_names:
            raise LookupError(field_name)
        return object()


class _FakeModel:
    objects = Mock()
    _meta = _MetaProxy(["email", "updated_at", "updated_by"])

    def __init__(self, email):
        self.email = email
        self.updated_at = None
        self.updated_by = None
        self.save = Mock()


class _FakeModelNoAudit:
    objects = Mock()
    _meta = _MetaProxy(["email"])

    def __init__(self, email):
        self.email = email
        self.save = Mock()


class _BulkChildDefaultSerializer(serializers.Serializer):
    pass


class BulkUpdateListSerializerTests(DrfCommonTestCase):
    def setUp(self):
        super().setUp()
        _FakeModel.objects.bulk_update = Mock()
        _FakeModelNoAudit.objects.bulk_update = Mock()

    def test_use_save_on_bulk_update_loops_instance_save(self):
        serializer = BulkUpdateListSerializer(
            child=_BulkChildDefaultSerializer(),
            context={"view": SimpleNamespace(use_save_on_bulk_update=True)},
        )
        instances = [_FakeModelNoAudit("old1@test.com"), _FakeModelNoAudit("old2@test.com")]
        payload = [{"email": "new1@test.com"}, {"email": "new2@test.com"}]

        updated = serializer.update(instances, payload)

        self.assertEqual(updated[0].email, "new1@test.com")
        self.assertEqual(updated[1].email, "new2@test.com")
        updated[0].save.assert_called_once_with()
        updated[1].save.assert_called_once_with()
        _FakeModelNoAudit.objects.bulk_update.assert_not_called()

    @patch("drf_commons.serializers.base.get_current_authenticated_user")
    @patch("drf_commons.serializers.base.timezone.now")
    def test_bulk_update_injects_missing_audit_fields(
        self, mock_now, mock_current_user
    ):
        serializer = BulkUpdateListSerializer(child=_BulkChildDefaultSerializer())
        current_user = SimpleNamespace(id=1, is_authenticated=True)
        now_value = datetime(2026, 2, 21, 12, 0, 0, tzinfo=dt_timezone.utc)
        mock_current_user.return_value = current_user
        mock_now.return_value = now_value

        instances = [_FakeModel("old1@test.com"), _FakeModel("old2@test.com")]
        payload = [{"email": "new1@test.com"}, {"email": "new2@test.com"}]

        serializer.update(instances, payload)

        self.assertEqual(instances[0].updated_at, now_value)
        self.assertEqual(instances[1].updated_at, now_value)
        self.assertEqual(instances[0].updated_by, current_user)
        self.assertEqual(instances[1].updated_by, current_user)
        _FakeModel.objects.bulk_update.assert_called_once()
        fields = set(_FakeModel.objects.bulk_update.call_args[0][1])
        self.assertEqual(fields, {"email", "updated_at", "updated_by"})

    @patch("drf_commons.serializers.base.get_current_authenticated_user")
    @patch("drf_commons.serializers.base.timezone.now")
    def test_bulk_update_does_not_override_audit_fields_provided_in_payload(
        self, mock_now, mock_current_user
    ):
        serializer = BulkUpdateListSerializer(child=_BulkChildDefaultSerializer())
        injected_user = SimpleNamespace(id=2, is_authenticated=True)
        provided_user = SimpleNamespace(id=9, is_authenticated=True)
        provided_time = datetime(2026, 1, 1, 8, 0, 0, tzinfo=dt_timezone.utc)
        mock_current_user.return_value = injected_user
        mock_now.return_value = datetime(2026, 2, 21, 12, 0, 0, tzinfo=dt_timezone.utc)

        instance = _FakeModel("old@test.com")
        payload = [
            {
                "email": "new@test.com",
                "updated_at": provided_time,
                "updated_by": provided_user,
            }
        ]

        serializer.update([instance], payload)

        self.assertEqual(instance.updated_at, provided_time)
        self.assertEqual(instance.updated_by, provided_user)

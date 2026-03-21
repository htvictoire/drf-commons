"""
Tests for bulk operation mixins.
"""

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import include, path

from rest_framework import viewsets
from rest_framework.routers import DefaultRouter
from rest_framework.test import APITestCase

from drf_commons.common_tests.base_cases import ViewTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.common_tests.models import SoftDeletableItem
from drf_commons.serializers.base import BaseModelSerializer
from drf_commons.views.mixins.bulk import (
    BulkCreateModelMixin,
    BulkDeleteModelMixin,
    BulkOperationMixin,
    BulkUpdateModelMixin,
)

User = get_user_model()


# ---------------------------------------------------------------------------
# Minimal ViewSets + router for integration tests
# ---------------------------------------------------------------------------

class UserSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = User
        fields = ["id", "username", "email"]


class SoftDeletableItemSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = SoftDeletableItem
        fields = ["id", "name", "is_active", "deleted_at"]


class BulkDeleteViewSet(viewsets.GenericViewSet, BulkDeleteModelMixin):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class SoftDeleteViewSet(viewsets.GenericViewSet, BulkDeleteModelMixin):
    queryset = SoftDeletableItem.objects.all()
    serializer_class = SoftDeletableItemSerializer


router = DefaultRouter()
router.register(r"users", BulkDeleteViewSet, basename="users")
router.register(r"items", SoftDeleteViewSet, basename="items")

urlpatterns = [
    path("api/", include(router.urls)),
]




# ---------------------------------------------------------------------------
# Unit tests — mixin methods without HTTP
# ---------------------------------------------------------------------------

class BulkOperationMixinTests(ViewTestCase):
    """Tests for BulkOperationMixin validation helpers."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_operation_mixin_exists(self):
        mixin = BulkOperationMixin()
        self.assertIsInstance(mixin, BulkOperationMixin)

    def test_get_bulk_batch_size_explicit(self):
        """When bulk_batch_size is set explicitly it is returned as-is."""
        mixin = BulkOperationMixin()
        mixin.bulk_batch_size = 42
        self.assertEqual(mixin.get_bulk_batch_size(), 42)

    def test_get_bulk_batch_size_falls_back_to_settings(self):
        """When bulk_batch_size is None the settings value is returned."""
        from drf_commons.common_conf import settings
        mixin = BulkOperationMixin()
        mixin.bulk_batch_size = None
        self.assertEqual(mixin.get_bulk_batch_size(), settings.BULK_OPERATION_BATCH_SIZE)


class BulkOperationValidationTests(ViewTestCase):
    """Tests for validate_bulk_data branches."""

    def _make_mixin(self, batch_size=100):
        mixin = BulkDeleteModelMixin()
        mixin.queryset = User.objects.none()
        mixin.bulk_batch_size = batch_size
        return mixin

    def test_validate_bulk_data_non_list_raises(self):
        from rest_framework.exceptions import ValidationError
        mixin = self._make_mixin()
        with self.assertRaises(ValidationError):
            mixin.validate_bulk_data({"key": "val"})

    def test_validate_bulk_data_empty_list_raises(self):
        from rest_framework.exceptions import ValidationError
        mixin = self._make_mixin()
        with self.assertRaises(ValidationError):
            mixin.validate_bulk_data([])

    def test_validate_bulk_data_exceeds_batch_size_raises(self):
        from rest_framework.exceptions import ValidationError
        mixin = self._make_mixin(batch_size=2)
        with self.assertRaises(ValidationError):
            mixin.validate_bulk_data([1, 2, 3])

    def test_validate_bulk_data_valid_passes(self):
        mixin = self._make_mixin(batch_size=10)
        mixin.validate_bulk_data([1, 2, 3])  # should not raise


class BulkDeleteValidationTests(ViewTestCase):
    """Tests for _validate_delete_ids branches."""

    def _make_mixin(self, batch_size=100):
        mixin = BulkDeleteModelMixin()
        mixin.queryset = User.objects.none()
        mixin.bulk_batch_size = batch_size
        return mixin

    def test_validate_delete_ids_non_list_raises(self):
        from rest_framework.exceptions import ValidationError
        mixin = self._make_mixin()
        with self.assertRaises(ValidationError):
            mixin._validate_delete_ids("not-a-list")

    def test_validate_delete_ids_empty_raises(self):
        from rest_framework.exceptions import ValidationError
        mixin = self._make_mixin()
        with self.assertRaises(ValidationError):
            mixin._validate_delete_ids([])

    def test_validate_delete_ids_exceeds_batch_raises(self):
        from rest_framework.exceptions import ValidationError
        mixin = self._make_mixin(batch_size=2)
        with self.assertRaises(ValidationError):
            mixin._validate_delete_ids([1, 2, 3])


class BulkDeleteMessageTests(ViewTestCase):
    """Tests for message helpers."""

    def _make_mixin(self):
        mixin = BulkDeleteModelMixin()
        mixin.queryset = User.objects.none()
        mixin.bulk_batch_size = 100
        return mixin

    def test_get_bulk_message_with_count(self):
        mixin = self._make_mixin()
        msg = mixin._get_bulk_message("delete", count=5)
        self.assertIn("5", msg)
        self.assertIn("delete", msg)

    def test_get_bulk_message_without_count(self):
        mixin = self._make_mixin()
        msg = mixin._get_bulk_message("delete", count=None)
        self.assertIn("delete", msg)
        self.assertNotIn("None", msg)

    def test_on_bulk_soft_delete_message(self):
        mixin = self._make_mixin()
        msg = mixin.on_bulk_soft_delete_message(3)
        self.assertIn("soft delete", msg)
        self.assertIn("3", msg)


class BulkCreateModelMixinTests(ViewTestCase):
    """Tests for BulkCreateModelMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_create_mixin_has_bulk_create_method(self):
        mixin = BulkCreateModelMixin()
        self.assertTrue(hasattr(mixin, "bulk_create"))


class BulkUpdateModelMixinTests(ViewTestCase):
    """Tests for BulkUpdateModelMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_update_mixin_has_bulk_update_method(self):
        mixin = BulkUpdateModelMixin()
        self.assertTrue(hasattr(mixin, "bulk_update"))

    def test_bulk_update_mixin_has_bulk_contract_validator(self):
        mixin = BulkUpdateModelMixin()
        self.assertTrue(hasattr(mixin, "_validate_bulk_direct_serializer_contract"))


# ---------------------------------------------------------------------------
# Integration tests — real HTTP requests
# ---------------------------------------------------------------------------

@override_settings(ROOT_URLCONF=__name__)
class BulkDeleteIntegrationTests(APITestCase):
    """Integration tests for bulk_delete endpoint."""

    def setUp(self):
        self.actor = UserFactory()
        self.client.force_authenticate(user=self.actor)

    def test_bulk_delete_success(self):
        u1 = UserFactory()
        u2 = UserFactory()
        response = self.client.delete(
            "/api/users/bulk_delete/", [u1.pk, u2.pk], format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(pk__in=[u1.pk, u2.pk]).exists())

    def test_bulk_delete_with_missing_ids(self):
        u1 = UserFactory()
        response = self.client.delete(
            "/api/users/bulk_delete/", [u1.pk, 99999999], format="json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["missing_count"], 1)

    def test_bulk_delete_validation_error_non_list(self):
        response = self.client.delete(
            "/api/users/bulk_delete/", {"bad": "data"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_bulk_delete_validation_error_empty_list(self):
        response = self.client.delete(
            "/api/users/bulk_delete/", [], format="json"
        )
        self.assertEqual(response.status_code, 400)


@override_settings(ROOT_URLCONF=__name__)
class BulkSoftDeleteIntegrationTests(APITestCase):
    """Integration tests for bulk_soft_delete using SoftDeletableItem model."""

    def setUp(self):
        self.actor = UserFactory()
        self.client.force_authenticate(user=self.actor)

    def test_bulk_soft_delete_success(self):
        i1 = SoftDeletableItem.objects.create(name="a")
        i2 = SoftDeletableItem.objects.create(name="b")
        response = self.client.delete(
            "/api/items/bulk-soft-delete/", [i1.pk, i2.pk], format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data["data"]["count"], 0)
        i1.refresh_from_db()
        self.assertFalse(i1.is_active)
        self.assertIsNotNone(i1.deleted_at)

    def test_bulk_soft_delete_with_missing_ids(self):
        i1 = SoftDeletableItem.objects.create(name="a")
        response = self.client.delete(
            "/api/items/bulk-soft-delete/", [i1.pk, 99999999], format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["missing_count"], 1)

    def test_bulk_soft_delete_no_found_ids(self):
        response = self.client.delete(
            "/api/items/bulk-soft-delete/", [99999999], format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["count"], 0)

    def test_bulk_soft_delete_validation_error(self):
        response = self.client.delete(
            "/api/items/bulk-soft-delete/", "not-a-list", format="json"
        )
        self.assertEqual(response.status_code, 400)

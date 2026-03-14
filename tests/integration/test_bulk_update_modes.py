"""
Integration tests for bulk update execution modes.
"""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.test import override_settings
from django.urls import include, path

from rest_framework.routers import DefaultRouter
from rest_framework.test import APITestCase
from rest_framework import viewsets

from drf_commons.common_tests.factories import UserFactory
from drf_commons.serializers.base import BaseModelSerializer
from drf_commons.views.mixins import BulkUpdateModelMixin

User = get_user_model()


class UserBulkSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class BulkUpdateDefaultModeViewSet(viewsets.GenericViewSet, BulkUpdateModelMixin):
    queryset = User.objects.all()
    serializer_class = UserBulkSerializer


class BulkUpdateSaveLoopViewSet(viewsets.GenericViewSet, BulkUpdateModelMixin):
    queryset = User.objects.all()
    serializer_class = UserBulkSerializer
    use_save_on_bulk_update = True


router = DefaultRouter()
router.register(r"bulk-update-default", BulkUpdateDefaultModeViewSet, basename="bulk-update-default")
router.register(r"bulk-update-save-loop", BulkUpdateSaveLoopViewSet, basename="bulk-update-save-loop")

urlpatterns = [
    path("api/", include(router.urls)),
]


@override_settings(ROOT_URLCONF=__name__)
class BulkUpdateExecutionModeTests(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from django.conf import settings

        settings.ROOT_URLCONF = __name__

    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def _build_payload(self, user1, user2):
        return [
            {"id": user1.id, "email": "mode_new1@test.com"},
            {"id": user2.id, "email": "mode_new2@test.com"},
        ]

    def test_default_bulk_update_mode_bypasses_post_save_signals(self):
        user1 = UserFactory(username="mode_default_user1", email="mode_old1@test.com")
        user2 = UserFactory(username="mode_default_user2", email="mode_old2@test.com")
        payload = self._build_payload(user1, user2)
        save_events = []

        def receiver(sender, instance, **kwargs):
            if sender is User and instance.pk in {user1.pk, user2.pk}:
                save_events.append(instance.pk)

        post_save.connect(receiver, sender=User, weak=False, dispatch_uid="bulk_update_default_mode_receiver")
        try:
            response = self.client.patch("/api/bulk-update-default/bulk-update/", payload, format="json")
        finally:
            post_save.disconnect(sender=User, dispatch_uid="bulk_update_default_mode_receiver")

        self.assertEqual(response.status_code, 200)
        user1.refresh_from_db()
        user2.refresh_from_db()
        self.assertEqual(user1.email, "mode_new1@test.com")
        self.assertEqual(user2.email, "mode_new2@test.com")
        self.assertEqual(save_events, [])

    def test_save_loop_bulk_update_mode_emits_post_save_signals(self):
        user1 = UserFactory(username="mode_loop_user1", email="mode_loop_old1@test.com")
        user2 = UserFactory(username="mode_loop_user2", email="mode_loop_old2@test.com")
        payload = self._build_payload(user1, user2)
        save_events = []

        def receiver(sender, instance, **kwargs):
            if sender is User and instance.pk in {user1.pk, user2.pk}:
                save_events.append(instance.pk)

        post_save.connect(receiver, sender=User, weak=False, dispatch_uid="bulk_update_save_loop_mode_receiver")
        try:
            response = self.client.patch("/api/bulk-update-save-loop/bulk-update/", payload, format="json")
        finally:
            post_save.disconnect(sender=User, dispatch_uid="bulk_update_save_loop_mode_receiver")

        self.assertEqual(response.status_code, 200)
        user1.refresh_from_db()
        user2.refresh_from_db()
        self.assertEqual(user1.email, "mode_new1@test.com")
        self.assertEqual(user2.email, "mode_new2@test.com")
        self.assertEqual(sorted(save_events), sorted([user1.pk, user2.pk]))

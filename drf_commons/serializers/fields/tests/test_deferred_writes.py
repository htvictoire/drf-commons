"""
Tests for deferred relation writes in configurable related fields.
"""

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from rest_framework import serializers

from drf_commons.common_tests.base_cases import SerializerTestCase
from drf_commons.serializers.base import BaseModelSerializer
from drf_commons.serializers.fields.many import ManyDataToIdField
from drf_commons.serializers.fields.single import DataToIdField


class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ["id", "app_label", "model"]


class PermissionSerializer(BaseModelSerializer):
    content_type = DataToIdField(
        queryset=ContentType.objects.all(),
        serializer_class=ContentTypeSerializer,
    )

    class Meta(BaseModelSerializer.Meta):
        model = Permission
        fields = ["id", "name", "codename", "content_type"]


class NestedPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "name", "codename"]


class ContentTypeWithPermissionsSerializer(BaseModelSerializer):
    permissions = ManyDataToIdField(
        source="permission_set",
        queryset=Permission.objects.all(),
        serializer_class=NestedPermissionSerializer,
        relation_write={
            "relation_kind": "reverse_fk",
            "write_order": "root_first",
            "child_link_field": "content_type",
            "sync_mode": "append",
        },
    )

    class Meta(BaseModelSerializer.Meta):
        model = ContentType
        fields = ["id", "app_label", "model", "permissions"]


class DeferredRelationWriteTests(SerializerTestCase):
    def test_nested_child_is_not_saved_during_validation(self):
        payload = {
            "name": "Can create tickets",
            # Missing codename intentionally to fail parent validation.
            "content_type": {"app_label": "audit_app", "model": "audit_ticket"},
        }

        serializer = PermissionSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertFalse(
            ContentType.objects.filter(
                app_label="audit_app", model="audit_ticket"
            ).exists()
        )

    def test_nested_child_is_saved_on_parent_save(self):
        payload = {
            "name": "Can close ticket",
            "codename": "can_close_ticket",
            "content_type": {"app_label": "audit_app", "model": "audit_ticket"},
        }

        serializer = PermissionSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertFalse(
            ContentType.objects.filter(
                app_label="audit_app", model="audit_ticket"
            ).exists()
        )

        permission = serializer.save()
        self.assertEqual(permission.codename, "can_close_ticket")
        self.assertEqual(permission.content_type.app_label, "audit_app")
        self.assertEqual(permission.content_type.model, "audit_ticket")

    def test_reverse_fk_root_first_creates_and_links_children(self):
        payload = {
            "app_label": "catalog",
            "model": "book",
            "permissions": [
                {"name": "Can publish book", "codename": "can_publish_book"},
                {"name": "Can archive book", "codename": "can_archive_book"},
            ],
        }

        serializer = ContentTypeWithPermissionsSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertFalse(
            Permission.objects.filter(codename="can_publish_book").exists()
        )

        content_type = serializer.save()
        self.assertEqual(content_type.permission_set.count(), 2)
        self.assertEqual(
            set(content_type.permission_set.values_list("codename", flat=True)),
            {"can_publish_book", "can_archive_book"},
        )

    def test_reverse_fk_root_first_relinks_existing_id_values(self):
        source_content_type = ContentType.objects.create(
            app_label="catalog_old", model="book"
        )
        movable_permission = Permission.objects.create(
            name="Can move book",
            codename="can_move_book",
            content_type=source_content_type,
        )

        payload = {
            "app_label": "catalog_new",
            "model": "book",
            "permissions": [movable_permission.id],
        }

        serializer = ContentTypeWithPermissionsSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        new_content_type = serializer.save()

        movable_permission.refresh_from_db()
        self.assertEqual(movable_permission.content_type_id, new_content_type.id)

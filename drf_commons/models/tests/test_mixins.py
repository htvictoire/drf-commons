"""
Tests for model mixins.
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.db import models
from django.test import override_settings
from django.utils import timezone

from drf_commons.common_tests.base_cases import ModelTestCase
from drf_commons.common_tests.factories import UserFactory

from ..mixins import SoftDeleteMixin, TimeStampMixin, UserActionMixin

User = get_user_model()


class UserActionModelForTesting(UserActionMixin):
    """Test model using UserActionMixin."""

    class Meta:
        app_label = "drf_commons"

    name = models.CharField(max_length=100)


class TimeStampModelForTesting(TimeStampMixin):
    """Test model using TimeStampMixin."""

    class Meta:
        app_label = "drf_commons"

    name = models.CharField(max_length=100)


class SoftDeleteModelForTesting(SoftDeleteMixin):
    """Test model using SoftDeleteMixin."""

    class Meta:
        app_label = "drf_commons"

    name = models.CharField(max_length=100)


class UserActionMixinTests(ModelTestCase):
    """Tests for UserActionMixin."""

    def test_mixin_fields_exist(self):
        """Test that UserActionMixin adds the correct fields."""
        model = UserActionModelForTesting()

        self.assertTrue(hasattr(model, "created_by"))
        self.assertTrue(hasattr(model, "updated_by"))

    def test_created_by_field_properties(self):
        """Test created_by field properties."""
        field = UserActionModelForTesting._meta.get_field("created_by")

        self.assertIsInstance(field, models.ForeignKey)
        self.assertEqual(field.remote_field.model, User)
        self.assertEqual(field.remote_field.on_delete, models.SET_NULL)
        self.assertTrue(field.null)
        self.assertTrue(field.blank)
        self.assertIn("created", field.remote_field.related_name)

    def test_updated_by_field_properties(self):
        """Test updated_by field properties."""
        field = UserActionModelForTesting._meta.get_field("updated_by")

        self.assertIsInstance(field, models.ForeignKey)
        self.assertEqual(field.remote_field.model, User)
        self.assertEqual(field.remote_field.on_delete, models.SET_NULL)
        self.assertTrue(field.null)
        self.assertTrue(field.blank)
        self.assertIn("updated", field.remote_field.related_name)

    def test_related_names_are_unique(self):
        """Test that related names use class name to avoid conflicts."""
        created_field = UserActionModelForTesting._meta.get_field("created_by")
        updated_field = UserActionModelForTesting._meta.get_field("updated_by")

        self.assertIn(
            "useractionmodelfortesting", created_field.remote_field.related_name.lower()
        )
        self.assertIn(
            "useractionmodelfortesting", updated_field.remote_field.related_name.lower()
        )

    def test_help_text_is_descriptive(self):
        """Test that fields have descriptive help text."""
        created_field = UserActionModelForTesting._meta.get_field("created_by")
        updated_field = UserActionModelForTesting._meta.get_field("updated_by")

        self.assertIn("created", created_field.help_text.lower())
        self.assertIn("updated", updated_field.help_text.lower())


class TimeStampMixinTests(ModelTestCase):
    """Tests for TimeStampMixin."""

    def test_mixin_fields_exist(self):
        """Test that TimeStampMixin adds the correct fields."""
        model = TimeStampModelForTesting()

        self.assertTrue(hasattr(model, "created_at"))
        self.assertTrue(hasattr(model, "updated_at"))

    def test_created_at_field_properties(self):
        """Test created_at field properties."""
        field = TimeStampModelForTesting._meta.get_field("created_at")

        self.assertIsInstance(field, models.DateTimeField)
        self.assertTrue(field.auto_now_add)
        self.assertFalse(field.auto_now)

    def test_updated_at_field_properties(self):
        """Test updated_at field properties."""
        field = TimeStampModelForTesting._meta.get_field("updated_at")

        self.assertIsInstance(field, models.DateTimeField)
        self.assertFalse(field.auto_now_add)
        self.assertTrue(field.auto_now)

    def test_help_text_is_descriptive(self):
        """Test that timestamp fields have descriptive help text."""
        created_field = TimeStampModelForTesting._meta.get_field("created_at")
        updated_field = TimeStampModelForTesting._meta.get_field("updated_at")

        self.assertIn("created", created_field.help_text.lower())
        self.assertIn("updated", updated_field.help_text.lower())


class SoftDeleteMixinTests(ModelTestCase):
    """Tests for SoftDeleteMixin."""

    def test_mixin_fields_exist(self):
        """Test that SoftDeleteMixin adds the correct fields."""
        model = SoftDeleteModelForTesting()

        self.assertTrue(hasattr(model, "deleted_at"))

    def test_deleted_at_field_properties(self):
        """Test deleted_at field properties."""
        field = SoftDeleteModelForTesting._meta.get_field("deleted_at")

        self.assertIsInstance(field, models.DateTimeField)
        self.assertTrue(field.null)
        self.assertTrue(field.blank)

    def test_is_deleted_property_false_by_default(self):
        """Test is_deleted property returns False for new instances."""
        model = SoftDeleteModelForTesting()

        self.assertFalse(model.is_deleted)

    def test_is_deleted_property_true_when_soft_deleted(self):
        """Test is_deleted property returns True when is_active is False."""
        model = SoftDeleteModelForTesting()
        model.deleted_at = timezone.now()
        model.is_active = False

        self.assertTrue(model.is_deleted)

    @patch.object(SoftDeleteModelForTesting, "save")
    def test_soft_delete_method(self, mock_save):
        """Test soft_delete method sets deleted_at and saves."""
        model = SoftDeleteModelForTesting()

        with patch("drf_commons.models.mixins.timezone.now") as mock_now:
            mock_time = timezone.now()
            mock_now.return_value = mock_time

            model.soft_delete()

            self.assertEqual(model.deleted_at, mock_time)
            mock_save.assert_called_once_with()

    @patch("drf_commons.models.mixins.get_current_authenticated_user")
    def test_user_action_mixin_save_calls_set_user_method(self, mock_get_user):
        """Test UserActionMixin save method calls set_created_by_and_updated_by."""
        user = UserFactory()
        mock_get_user.return_value = user

        model = UserActionModelForTesting(name="test")

        with patch.object(model, "set_created_by_and_updated_by") as mock_set_user:
            with patch("django.db.models.Model.save") as mock_super_save:
                model.save()

                mock_set_user.assert_called_once()
                mock_super_save.assert_called_once()

    @patch("drf_commons.models.mixins.get_current_authenticated_user")
    def test_set_created_by_and_updated_by_new_instance(self, mock_get_user):
        """Test set_created_by_and_updated_by for new instances."""
        user = UserFactory()
        with patch.object(type(user), 'is_authenticated', new_callable=lambda: property(lambda self: True)):
            mock_get_user.return_value = user

            model = UserActionModelForTesting(name="test")

            model.set_created_by_and_updated_by()

            self.assertEqual(model.created_by, user)
            self.assertEqual(model.updated_by, user)

    @patch("drf_commons.models.mixins.get_current_authenticated_user")
    def test_set_created_by_and_updated_by_existing_instance(self, mock_get_user):
        """Test set_created_by_and_updated_by for existing instances."""
        original_user = UserFactory()
        current_user = UserFactory()
        with patch.object(type(current_user), 'is_authenticated', new_callable=lambda: property(lambda self: True)):
            mock_get_user.return_value = current_user

            model = UserActionModelForTesting(name="test")
            model.created_by = original_user

            model.set_created_by_and_updated_by()

            self.assertEqual(model.created_by, original_user)
            self.assertEqual(model.updated_by, current_user)

    @patch("drf_commons.models.mixins.get_current_authenticated_user")
    def test_set_created_by_and_updated_by_no_user(self, mock_get_user):
        """Test set_created_by_and_updated_by when no current user."""
        mock_get_user.return_value = None

        model = UserActionModelForTesting(name="test")

        model.set_created_by_and_updated_by()

        self.assertIsNone(model.created_by)
        self.assertIsNone(model.updated_by)

    @patch("drf_commons.models.mixins.get_current_authenticated_user")
    def test_set_created_by_and_updated_by_unauthenticated_user(self, mock_get_user):
        """Test set_created_by_and_updated_by when user is not authenticated."""
        # Helper contract: unauthenticated user resolves to None.
        mock_get_user.return_value = None

        model = UserActionModelForTesting(name="test")

        model.set_created_by_and_updated_by()

        self.assertIsNone(model.created_by)
        self.assertIsNone(model.updated_by)

    @patch.object(SoftDeleteModelForTesting, "save")
    def test_restore_method(self, mock_save):
        """Test restore method clears deleted_at and saves."""
        model = SoftDeleteModelForTesting()
        model.deleted_at = timezone.now()

        model.restore()

        self.assertIsNone(model.deleted_at)
        mock_save.assert_called_once_with()

    def test_soft_delete_restore_cycle(self):
        """Test complete soft delete and restore cycle."""
        model = SoftDeleteModelForTesting()

        # Initially not deleted
        self.assertFalse(model.is_deleted)
        self.assertIsNone(model.deleted_at)

        # After soft delete
        with patch.object(model, "save"):
            model.soft_delete()

        self.assertTrue(model.is_deleted)
        self.assertIsNotNone(model.deleted_at)

        # After restore
        with patch.object(model, "save"):
            model.restore()

        self.assertFalse(model.is_deleted)
        self.assertIsNone(model.deleted_at)

    def test_help_text_is_descriptive(self):
        """Test that deleted_at field has descriptive help text."""
        field = SoftDeleteModelForTesting._meta.get_field("deleted_at")

        self.assertIn("soft deleted", field.help_text.lower())

    def test_user_action_mixin_init_method_exists(self):
        """Test UserActionMixin has __init__ method that can be instantiated."""
        # This test ensures the decorator doesn't break instantiation
        model = UserActionModelForTesting(name="test")
        self.assertIsNotNone(model)
        self.assertEqual(model.name, "test")

    @override_settings(MIDDLEWARE=["django.middleware.security.SecurityMiddleware"])
    def test_user_action_no_runtime_middleware_check_on_save_path(self):
        """Attribution logic does not enforce middleware at save-time."""
        model = UserActionModelForTesting(name="test")
        model.set_created_by_and_updated_by()

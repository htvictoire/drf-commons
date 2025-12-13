"""
Tests for custom model fields.
"""

import warnings
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.conf import settings as django_settings
from django.db import models

from drf_commons.common_tests.base_cases import ModelTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.current_user.utils import get_current_authenticated_user

from ..fields import CurrentUserField

User = get_user_model()


class CurrentUserFieldTests(ModelTestCase):
    """Tests for CurrentUserField."""

    def test_field_initialization_defaults(self):
        """Test CurrentUserField initialization with default values."""
        field = CurrentUserField()

        self.assertFalse(field.on_update)
        self.assertTrue(field.null)
        self.assertEqual(field.remote_field.model, django_settings.AUTH_USER_MODEL)
        self.assertEqual(field.remote_field.on_delete, models.CASCADE)

    def test_field_initialization_with_on_update(self):
        """Test CurrentUserField initialization with on_update=True."""
        field = CurrentUserField(on_update=True)

        self.assertTrue(field.on_update)
        self.assertFalse(field.editable)
        self.assertTrue(field.blank)

    def test_field_initialization_with_custom_on_delete(self):
        """Test CurrentUserField initialization with custom on_delete."""
        field = CurrentUserField(on_delete=models.SET_NULL)

        self.assertEqual(field.remote_field.on_delete, models.SET_NULL)

    def test_field_initialization_normalizes_to_parameter(self):
        """Test that 'to' parameter is normalized."""
        field = CurrentUserField(to="AUTH.USER")

        self.assertEqual(field.remote_field.model, django_settings.AUTH_USER_MODEL)

    def test_field_warns_for_shadowing_args(self):
        """Test that field warns when shadowing default arguments."""
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            CurrentUserField("some_arg")

            self.assertEqual(len(warning_list), 1)
            self.assertIn("will be ignored", str(warning_list[0].message))

    def test_field_warns_for_shadowing_kwargs(self):
        """Test that field warns when shadowing default kwargs."""
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            CurrentUserField(null=False)

            self.assertEqual(len(warning_list), 1)
            self.assertIn("will be ignored", str(warning_list[0].message))

    def test_field_no_warning_for_matching_defaults(self):
        """Test that field doesn't warn when kwargs match defaults."""
        with warnings.catch_warnings(record=True) as warning_list:
            warnings.simplefilter("always")

            CurrentUserField(null=True)

            self.assertEqual(len(warning_list), 0)

    def test_deconstruct_without_on_update(self):
        """Test field deconstruction without on_update."""
        field = CurrentUserField()
        _, path, _, kwargs = field.deconstruct()

        self.assertEqual(path, "models.fields.CurrentUserField")
        self.assertNotIn("on_update", kwargs)

    def test_deconstruct_with_on_update(self):
        """Test field deconstruction with on_update."""
        field = CurrentUserField(on_update=True)
        _, path, _, kwargs = field.deconstruct()

        self.assertEqual(path, "models.fields.CurrentUserField")
        self.assertTrue(kwargs["on_update"])
        self.assertNotIn("editable", kwargs)
        self.assertNotIn("blank", kwargs)

    @patch("models.fields.get_current_authenticated_user")
    def test_pre_save_without_on_update(self, mock_get_user):
        """Test pre_save behavior when on_update=False."""
        user = UserFactory()
        mock_get_user.return_value = user

        field = CurrentUserField()
        field.set_attributes_from_name("created_by")

        class TestModel:
            pass

        instance = TestModel()

        with patch.object(
            models.ForeignKey, "pre_save", return_value=user.pk
        ) as mock_parent:
            field.pre_save(instance, add=True)
            mock_parent.assert_called_once_with(instance, True)

    @patch("models.fields.get_current_authenticated_user")
    def test_pre_save_with_on_update(self, mock_get_user):
        """Test pre_save behavior when on_update=True."""
        user = UserFactory()
        mock_get_user.return_value = user

        field = CurrentUserField(on_update=True)
        field.set_attributes_from_name("updated_by")

        class TestModel:
            pass

        instance = TestModel()

        result = field.pre_save(instance, add=True)

        self.assertEqual(result, user.pk)
        self.assertEqual(getattr(instance, field.attname), user.pk)

    @patch("models.fields.get_current_authenticated_user")
    def test_pre_save_with_on_update_no_user(self, mock_get_user):
        """Test pre_save behavior when on_update=True and no current user."""
        mock_get_user.return_value = None

        field = CurrentUserField(on_update=True)
        field.set_attributes_from_name("updated_by")

        class TestModel:
            pass

        instance = TestModel()

        result = field.pre_save(instance, add=True)

        self.assertIsNone(result)
        self.assertIsNone(getattr(instance, field.attname))

    def test_field_description(self):
        """Test field description for help text."""
        field = CurrentUserField()

        self.assertIn("current logged in user", str(field.description))

    def test_field_default_value_callable(self):
        """Test field default value is properly set to callable."""
        field = CurrentUserField()

        self.assertEqual(field.default, get_current_authenticated_user)

    def test_field_related_name_generation(self):
        """Test that field properly inherits ForeignKey related name behavior."""
        field = CurrentUserField(related_name="custom_related")

        self.assertEqual(field.remote_field.related_name, "custom_related")

    def test_field_help_text_inheritance(self):
        """Test field can accept custom help_text."""
        custom_help = "Custom help text for this field"
        field = CurrentUserField(help_text=custom_help)

        self.assertEqual(field.help_text, custom_help)

    def test_field_initialization_with_middleware_requirement(self):
        """Test CurrentUserField can be instantiated with middleware requirement."""
        field = CurrentUserField()

        self.assertIsInstance(field, models.ForeignKey)
        self.assertEqual(field.remote_field.model, django_settings.AUTH_USER_MODEL)
        self.assertFalse(field.on_update)

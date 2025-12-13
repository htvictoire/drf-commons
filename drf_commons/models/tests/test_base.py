"""
Tests for base model functionality.
"""

import json
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from drf_commons.common_tests.base_cases import ModelTestCase
from drf_commons.common_tests.factories import UserFactory

from ..base import BaseModelMixin

User = get_user_model()


class BaseModelForTesting(BaseModelMixin):
    """Test model using BaseModelMixin."""

    class Meta(BaseModelMixin.Meta):
        app_label = "drf_commons"

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)


class BaseModelMixinTests(ModelTestCase):
    """Tests for BaseModelMixin."""

    def test_model_has_uuid_primary_key(self):
        """Test that model uses UUID as primary key."""
        model = BaseModelForTesting()

        self.assertIsInstance(model.id, uuid.UUID)
        self.assertTrue(model._meta.get_field("id").primary_key)
        self.assertFalse(model._meta.get_field("id").editable)

    def test_model_inherits_user_action_mixin(self):
        """Test that model inherits UserActionMixin fields."""
        model = BaseModelForTesting()

        self.assertTrue(hasattr(model, "created_by"))
        self.assertTrue(hasattr(model, "updated_by"))

    def test_model_inherits_timestamp_mixin(self):
        """Test that model inherits TimeStampMixin fields."""
        model = BaseModelForTesting()

        self.assertTrue(hasattr(model, "created_at"))
        self.assertTrue(hasattr(model, "updated_at"))

    def test_model_meta_configuration(self):
        """Test model meta configuration."""
        meta = BaseModelForTesting._meta

        self.assertFalse(meta.abstract)
        self.assertEqual(meta.ordering, ["-created_at"])
        self.assertEqual(meta.get_latest_by, "-created_at")

    def test_get_json_basic(self):
        """Test basic JSON serialization."""
        model = BaseModelForTesting(name="test", description="test description")
        model.id = uuid.uuid4()

        json_str = model.get_json()
        data = json.loads(json_str)

        self.assertEqual(data["name"], "test")
        self.assertEqual(data["description"], "test description")
        self.assertEqual(data["id"], str(model.id))

    def test_get_json_with_exclude_fields(self):
        """Test JSON serialization with excluded fields."""
        model = BaseModelForTesting(name="test", description="test description")

        json_str = model.get_json(exclude_fields=["description"])
        data = json.loads(json_str)

        self.assertIn("name", data)
        self.assertNotIn("description", data)

    def test_get_json_with_specific_fields(self):
        """Test JSON serialization with specific fields only."""
        model = BaseModelForTesting(name="test", description="test description")

        json_str = model.get_json(fields=["name"])
        data = json.loads(json_str)

        self.assertIn("name", data)
        self.assertNotIn("description", data)

    def test_get_json_exclude_general_fields(self):
        """Test JSON serialization excluding general fields."""
        model = BaseModelForTesting(name="test", description="test description")

        json_str = model.get_json(exclude_general_fields=True)
        data = json.loads(json_str)

        self.assertIn("name", data)
        self.assertIn("description", data)
        self.assertNotIn("created_at", data)
        self.assertNotIn("updated_at", data)
        self.assertNotIn("created_by", data)
        self.assertNotIn("updated_by", data)

    def test_get_json_with_foreign_key_fields(self):
        """Test JSON serialization handles foreign key fields."""
        user = UserFactory()
        model = BaseModelForTesting(name="test")
        model.created_by = user

        json_str = model.get_json()
        data = json.loads(json_str)

        self.assertEqual(data["created_by"], user.pk)

    def test_get_json_handles_datetime_fields(self):
        """Test JSON serialization handles datetime fields."""
        model = BaseModelForTesting(name="test")
        test_time = timezone.now()
        model.created_at = test_time
        model.updated_at = test_time

        json_str = model.get_json()
        data = json.loads(json_str)

        self.assertIsInstance(data, dict)
        self.assertIn("created_at", data)
        self.assertIn("updated_at", data)

    def test_id_field_properties(self):
        """Test UUID ID field properties."""
        field = BaseModelForTesting._meta.get_field("id")

        self.assertIsInstance(field, models.UUIDField)
        self.assertEqual(field.default, uuid.uuid4)
        self.assertTrue(field.primary_key)
        self.assertFalse(field.editable)
        self.assertIn("identifier", field.help_text.lower())

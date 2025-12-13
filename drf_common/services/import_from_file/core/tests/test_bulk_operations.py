"""
Tests for BulkOperations class.

Tests bulk database operations functionality.
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model

from drf_common.common_tests.base_cases import DrfCommonTestCase

from ..bulk_operations import BulkOperations

User = get_user_model()


class BulkOperationsTests(DrfCommonTestCase):
    """Tests for BulkOperations."""

    def setUp(self):
        super().setUp()
        self.bulk_ops = BulkOperations()

    def test_bulk_operations_initialization_default_batch_size(self):
        """Test bulk operations initializes with default batch size."""
        bulk_ops = BulkOperations()
        self.assertEqual(bulk_ops.batch_size, 250)

    def test_bulk_operations_initialization_custom_batch_size(self):
        """Test bulk operations initializes with custom batch size."""
        bulk_ops = BulkOperations(batch_size=100)
        self.assertEqual(bulk_ops.batch_size, 100)

    def test_individual_create_instances_with_empty_list(self):
        """Test individual_create_instances with empty list."""
        result = self.bulk_ops.individual_create_instances(User, [], [], "test_step")
        self.assertEqual(result, {})

    def test_individual_create_instances_with_valid_instances(self):
        """Test individual_create_instances with valid instances."""
        user1 = User(username="testuser1", email="test1@example.com")
        user2 = User(username="testuser2", email="test2@example.com")
        to_create = [(0, user1), (1, user2)]
        created_objs = []

        result = self.bulk_ops.individual_create_instances(
            User, to_create, created_objs, "test_step"
        )

        # Should return empty dict if all saves successful
        self.assertIsInstance(result, dict)

    def test_individual_create_instances_with_multiple_users(self):
        """Test individual_create_instances creates multiple users successfully."""
        # User instances
        user1 = User(username="testuser1")
        user2 = User(username="testuser2")

        to_create = [(0, user1), (1, user2)]
        created_objs = [{}, {}]

        result = self.bulk_ops.individual_create_instances(
            User, to_create, created_objs, "test_step"
        )

        # Verify no errors occurred
        self.assertEqual(result, {})

        # Verify both users were saved and added to created_objs
        self.assertIn("test_step", created_objs[0])
        self.assertEqual(created_objs[0]["test_step"], user1)
        self.assertIsNotNone(user1.pk)

        self.assertIn("test_step", created_objs[1])
        self.assertEqual(created_objs[1]["test_step"], user2)
        self.assertIsNotNone(user2.pk)


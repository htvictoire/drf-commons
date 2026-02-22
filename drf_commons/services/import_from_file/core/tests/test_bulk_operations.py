"""
Tests for BulkOperations class.

Tests bulk database operations functionality.
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from drf_commons.common_tests.base_cases import DrfCommonTestCase

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

    def test_bulk_update_instances_returns_row_errors_when_fallback_saves_fail(self):
        """bulk_update_instances should return per-row errors when fallback saves fail."""
        user1 = User.objects.create(username="update_fail_1")
        user2 = User.objects.create(username="update_fail_2")
        user1.email = "new1@example.com"
        user2.email = "new2@example.com"

        user1.save = Mock(side_effect=Exception("db write failed"))
        user2.save = Mock(return_value=None)

        with patch.object(User.objects, "bulk_update", side_effect=Exception("bulk failed")):
            result = self.bulk_ops.bulk_update_instances(
                User,
                [(10, user1), (11, user2)],
                {"email"},
            )

        self.assertEqual(set(result.keys()), {10})
        self.assertIn("Failed to update User", result[10])

    def test_bulk_update_instances_returns_empty_when_nothing_to_update(self):
        """bulk_update_instances should return empty errors for no-op input."""
        result = self.bulk_ops.bulk_update_instances(User, [], {"email"})
        self.assertEqual(result, {})

        user = User.objects.create(username="no_fields_to_update")
        result = self.bulk_ops.bulk_update_instances(User, [(0, user)], set())
        self.assertEqual(result, {})

    def test_bulk_create_instances_uses_bulk_path_on_success(self):
        """bulk_create_instances should use bulk path and avoid fallback saves on success."""
        user1 = User(username="bulk_create_ok_1", email="ok1@test.com")
        user2 = User(username="bulk_create_ok_2", email="ok2@test.com")
        to_create = [(0, user1), (1, user2)]
        created_objs = [{}, {}]

        # If fallback path is used, these mocks will raise.
        user1.save = Mock(side_effect=AssertionError("fallback save should not run"))
        user2.save = Mock(side_effect=AssertionError("fallback save should not run"))

        result = self.bulk_ops.bulk_create_instances(
            User, to_create, created_objs, "test_step"
        )

        self.assertEqual(result, {})
        self.assertIn("test_step", created_objs[0])
        self.assertIn("test_step", created_objs[1])

    def test_bulk_create_instances_falls_back_on_bulk_errors(self):
        """bulk_create_instances should fall back to per-row saves when bulk create fails."""
        user1 = User(username="bulk_create_fb_1", email="fb1@test.com")
        user2 = User(username="bulk_create_fb_2", email="fb2@test.com")
        to_create = [(0, user1), (1, user2)]
        created_objs = [{}, {}]

        user1.save = Mock(return_value=None)
        user2.save = Mock(side_effect=Exception("fallback row failure"))

        with patch.object(
            User.objects, "bulk_create", side_effect=Exception("bulk create failure")
        ):
            result = self.bulk_ops.bulk_create_instances(
                User, to_create, created_objs, "test_step"
            )

        self.assertIn(1, result)
        self.assertIn("Failed to save User", result[1])
        self.assertIn("test_step", created_objs[0])
        self.assertNotIn("test_step", created_objs[1])

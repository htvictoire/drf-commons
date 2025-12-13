"""
Tests for bulk operation mixins.

Tests bulk operation mixins functionality.
"""


from django.contrib.auth import get_user_model

from drf_common.common_tests.base_cases import ViewTestCase
from drf_common.common_tests.factories import UserFactory

from ..bulk import (
    BulkCreateModelMixin,
    BulkDeleteModelMixin,
    BulkOperationMixin,
    BulkUpdateModelMixin,
)

User = get_user_model()


class BulkOperationMixinTests(ViewTestCase):
    """Tests for BulkOperationMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_operation_mixin_exists(self):
        """Test BulkOperationMixin can be instantiated."""
        mixin = BulkOperationMixin()
        self.assertIsInstance(mixin, BulkOperationMixin)


class BulkCreateModelMixinTests(ViewTestCase):
    """Tests for BulkCreateModelMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_create_mixin_has_bulk_create_method(self):
        """Test BulkCreateModelMixin has bulk_create method."""
        mixin = BulkCreateModelMixin()
        self.assertTrue(hasattr(mixin, "bulk_create"))

    def test_bulk_create_mixin_has_bulk_create_method_only(self):
        """Test BulkCreateModelMixin has bulk_create method."""
        mixin = BulkCreateModelMixin()
        self.assertTrue(hasattr(mixin, "bulk_create"))


class BulkUpdateModelMixinTests(ViewTestCase):
    """Tests for BulkUpdateModelMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_update_mixin_has_bulk_update_method(self):
        """Test BulkUpdateModelMixin has bulk_update method."""
        mixin = BulkUpdateModelMixin()
        self.assertTrue(hasattr(mixin, "bulk_update"))

    def test_bulk_update_mixin_has_bulk_update_method_only(self):
        """Test BulkUpdateModelMixin has bulk_update method."""
        mixin = BulkUpdateModelMixin()
        self.assertTrue(hasattr(mixin, "bulk_update"))


class BulkDeleteModelMixinTests(ViewTestCase):
    """Tests for BulkDeleteModelMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_delete_mixin_has_bulk_delete_method(self):
        """Test BulkDeleteModelMixin has bulk_delete method."""
        mixin = BulkDeleteModelMixin()
        self.assertTrue(hasattr(mixin, "bulk_delete"))

    def test_bulk_delete_mixin_has_bulk_delete_and_soft_delete_methods(self):
        """Test BulkDeleteModelMixin has bulk_delete and bulk_soft_delete methods."""
        mixin = BulkDeleteModelMixin()
        self.assertTrue(hasattr(mixin, "bulk_delete"))
        self.assertTrue(hasattr(mixin, "bulk_soft_delete"))

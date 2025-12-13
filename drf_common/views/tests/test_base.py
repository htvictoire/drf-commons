"""
Tests for base viewset classes.

Tests viewset classes that combine mixins for various use cases.
"""

from django.contrib.auth import get_user_model

from rest_framework import viewsets

from drf_common.common_tests.base_cases import ViewTestCase
from drf_common.common_tests.factories import UserFactory

from ..base import (
    BaseViewSet,
    BulkCreateViewSet,
    BulkDeleteViewSet,
    BulkImportableViewSet,
    BulkOnlyViewSet,
    BulkUpdateViewSet,
    BulkViewSet,
    CreateListViewSet,
    ImportableViewSet,
    ReadOnlyViewSet,
)

User = get_user_model()


class BaseViewSetTests(ViewTestCase):
    """Tests for BaseViewSet."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_base_viewset_inheritance(self):
        """Test BaseViewSet inherits from correct classes."""
        viewset = BaseViewSet()
        self.assertIsInstance(viewset, viewsets.GenericViewSet)

    def test_base_viewset_default_attributes(self):
        """Test BaseViewSet has correct default attributes."""
        viewset = BaseViewSet()
        self.assertTrue(viewset.return_data_on_create)
        self.assertTrue(viewset.return_data_on_update)

    def test_base_viewset_has_required_mixins(self):
        """Test BaseViewSet has all required mixins."""
        viewset = BaseViewSet()
        # Check that it has methods from all the mixins
        self.assertTrue(hasattr(viewset, "create"))
        self.assertTrue(hasattr(viewset, "list"))
        self.assertTrue(hasattr(viewset, "retrieve"))
        self.assertTrue(hasattr(viewset, "update"))
        self.assertTrue(hasattr(viewset, "destroy"))


class BulkViewSetTests(ViewTestCase):
    """Tests for BulkViewSet."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_viewset_inheritance(self):
        """Test BulkViewSet inherits from BaseViewSet."""
        viewset = BulkViewSet()
        self.assertIsInstance(viewset, BaseViewSet)

    def test_bulk_viewset_has_bulk_methods(self):
        """Test BulkViewSet has bulk operation methods."""
        viewset = BulkViewSet()
        self.assertTrue(hasattr(viewset, "bulk_create"))
        self.assertTrue(hasattr(viewset, "bulk_update"))
        self.assertTrue(hasattr(viewset, "bulk_delete"))


class ReadOnlyViewSetTests(ViewTestCase):
    """Tests for ReadOnlyViewSet."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_readonly_viewset_inheritance(self):
        """Test ReadOnlyViewSet inherits from correct classes."""
        viewset = ReadOnlyViewSet()
        self.assertIsInstance(viewset, viewsets.GenericViewSet)

    def test_readonly_viewset_has_read_methods(self):
        """Test ReadOnlyViewSet has read operation methods."""
        viewset = ReadOnlyViewSet()
        self.assertTrue(hasattr(viewset, "list"))
        self.assertTrue(hasattr(viewset, "retrieve"))


class CreateListViewSetTests(ViewTestCase):
    """Tests for CreateListViewSet."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_create_list_viewset_has_create_list_methods(self):
        """Test CreateListViewSet has create and list methods."""
        viewset = CreateListViewSet()
        self.assertTrue(hasattr(viewset, "create"))
        self.assertTrue(hasattr(viewset, "list"))


class BulkCreateViewSetTests(ViewTestCase):
    """Tests for BulkCreateViewSet."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_create_viewset_has_bulk_create_method(self):
        """Test BulkCreateViewSet has bulk_create method."""
        viewset = BulkCreateViewSet()
        self.assertTrue(hasattr(viewset, "bulk_create"))


class BulkUpdateViewSetTests(ViewTestCase):
    """Tests for BulkUpdateViewSet."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_update_viewset_has_bulk_update_method(self):
        """Test BulkUpdateViewSet has bulk_update method."""
        viewset = BulkUpdateViewSet()
        self.assertTrue(hasattr(viewset, "bulk_update"))


class BulkDeleteViewSetTests(ViewTestCase):
    """Tests for BulkDeleteViewSet."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_delete_viewset_has_bulk_delete_method(self):
        """Test BulkDeleteViewSet has bulk_delete method."""
        viewset = BulkDeleteViewSet()
        self.assertTrue(hasattr(viewset, "bulk_delete"))


class BulkOnlyViewSetTests(ViewTestCase):
    """Tests for BulkOnlyViewSet."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_only_viewset_has_bulk_methods(self):
        """Test BulkOnlyViewSet has all bulk methods."""
        viewset = BulkOnlyViewSet()
        self.assertTrue(hasattr(viewset, "bulk_create"))
        self.assertTrue(hasattr(viewset, "bulk_update"))
        self.assertTrue(hasattr(viewset, "bulk_delete"))


class ImportableViewSetTests(ViewTestCase):
    """Tests for ImportableViewSet."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_importable_viewset_has_import_method(self):
        """Test ImportableViewSet has file import method."""
        viewset = ImportableViewSet()
        self.assertTrue(hasattr(viewset, "import_file"))


class BulkImportableViewSetTests(ViewTestCase):
    """Tests for BulkImportableViewSet."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_bulk_importable_viewset_has_bulk_and_import_methods(self):
        """Test BulkImportableViewSet has both bulk and import methods."""
        viewset = BulkImportableViewSet()
        self.assertTrue(hasattr(viewset, "bulk_create"))
        self.assertTrue(hasattr(viewset, "bulk_update"))
        self.assertTrue(hasattr(viewset, "bulk_delete"))
        self.assertTrue(hasattr(viewset, "import_file"))

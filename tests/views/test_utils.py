"""
Tests for utility functions.

Tests utility functions used in view mixins.
"""

from unittest.mock import Mock

from django.contrib.auth import get_user_model

from drf_commons.common_tests.base_cases import ViewTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.views.mixins.utils import get_model_name, get_operation_message

User = get_user_model()


class UtilsTests(ViewTestCase):
    """Tests for utility functions."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_get_model_name_with_model_class(self):
        """Test get_model_name with model class."""

        class MockViewSet:
            def get_queryset(self):
                return User.objects.none()

        viewset = MockViewSet()
        result = get_model_name(viewset)
        self.assertIsInstance(result, str)

    def test_get_model_name_with_mock_object(self):
        """Test get_model_name with mock object."""
        mock_viewset = Mock()
        mock_queryset = Mock()
        mock_model = Mock()
        mock_meta = Mock()
        mock_meta.verbose_name_plural = "test models"
        mock_model._meta = mock_meta
        mock_model.__name__ = "TestModel"
        mock_queryset.model = mock_model
        mock_viewset.queryset = mock_queryset

        result = get_model_name(mock_viewset)
        self.assertEqual(result, "Test Models")

    def test_get_model_name_handles_exception(self):
        """Test get_model_name handles exceptions gracefully."""
        mock_viewset = Mock()
        mock_viewset.queryset = None
        mock_viewset.model = None

        result = get_model_name(mock_viewset)
        # Should return the fallback value "Objects"
        self.assertEqual(result, "Objects")

    def test_get_model_name_uses_model_attribute_when_no_queryset(self):
        mock_viewset = Mock(spec=[])
        mock_meta = Mock()
        mock_meta.verbose_name_plural = "test items"
        mock_model = Mock()
        mock_model._meta = mock_meta
        mock_viewset.model = mock_model

        result = get_model_name(mock_viewset)
        self.assertEqual(result, "Test Items")

    def test_get_model_name_falls_back_to_class_name_when_no_verbose_plural(self):
        mock_viewset = Mock(spec=[])
        mock_meta = Mock()
        mock_meta.verbose_name_plural = None
        mock_model = Mock()
        mock_model._meta = mock_meta
        mock_model.__name__ = "Widget"
        mock_viewset.model = mock_model

        result = get_model_name(mock_viewset)
        self.assertEqual(result, "Widget")


class GetOperationMessageTests(ViewTestCase):
    """Tests for get_operation_message()."""

    def test_message_with_count_includes_count(self):
        mock_viewset = Mock()
        mock_viewset.queryset = None
        mock_viewset.model = None

        result = get_operation_message(mock_viewset, "created", count=5)
        self.assertIn("5", result)
        self.assertIn("Created", result)

    def test_message_without_count_uses_generic_format(self):
        mock_viewset = Mock()
        mock_viewset.queryset = None
        mock_viewset.model = None

        result = get_operation_message(mock_viewset, "deleted")
        self.assertIn("Deleted", result)
        self.assertNotIn("None", result)

    def test_message_with_prefix_includes_prefix(self):
        mock_viewset = Mock()
        mock_viewset.queryset = None
        mock_viewset.model = None

        result = get_operation_message(mock_viewset, "updated", count=3, operation_prefix="Bulk")
        self.assertIn("Bulk", result)
        self.assertIn("3", result)

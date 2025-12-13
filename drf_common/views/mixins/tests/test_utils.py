"""
Tests for utility functions.

Tests utility functions used in view mixins.
"""

from unittest.mock import Mock

from django.contrib.auth import get_user_model

from drf_common.common_tests.base_cases import ViewTestCase
from drf_common.common_tests.factories import UserFactory

from ..utils import get_model_name

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

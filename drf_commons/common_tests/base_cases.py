"""
Base test case classes for DRF Commons library tests.
"""

from unittest.mock import Mock

from django.test import TestCase, TransactionTestCase

from rest_framework.test import APITestCase

from drf_commons.current_user.utils import _clear_current_user
from .utils import mock_current_user


class DrfCommonTestCase(TestCase):
    """Base test case for DRF Commons tests."""

    def setUp(self):
        super().setUp()
        self.addCleanup(self._cleanup_current_user_context)

    def _cleanup_current_user_context(self):
        """Clean up current-user context after test."""
        _clear_current_user()


class DrfCommonTransactionTestCase(TransactionTestCase):
    """Base transaction test case for DRF Commons tests."""

    def setUp(self):
        super().setUp()
        self.addCleanup(self._cleanup_current_user_context)

    def _cleanup_current_user_context(self):
        """Clean up current-user context after test."""
        _clear_current_user()


class DrfCommonAPITestCase(APITestCase):
    """Base API test case for DRF Commons API tests."""

    def setUp(self):
        super().setUp()
        self.addCleanup(self._cleanup_current_user_context)

    def _cleanup_current_user_context(self):
        """Clean up current-user context after test."""
        _clear_current_user()


class ModelTestCase(DrfCommonTestCase):
    """Base test case for model tests."""

    def setUp(self):
        super().setUp()
        self.user = None

    def set_current_user(self, user):
        """Set current user context for testing."""
        self.user = user
        mock_current_user(user)


class SerializerTestCase(DrfCommonTestCase):
    """Base test case for serializer tests."""

    def setUp(self):
        super().setUp()
        self.user = None
        self.request_context = {}

    def get_serializer_context(self, **kwargs):
        """Get serializer context with user and request."""
        context = {"request": self.create_mock_request()}
        context.update(self.request_context)
        context.update(kwargs)
        return context

    def create_mock_request(self):
        """Create mock request object."""
        request = Mock()
        request.user = self.user
        request.query_params = {}
        return request


class ViewTestCase(DrfCommonAPITestCase):
    """Base test case for view tests."""

    def setUp(self):
        super().setUp()
        self.user = None

    def authenticate(self, user):
        """Authenticate API client with user."""
        self.user = user
        self.client.force_authenticate(user=user)
        mock_current_user(user)

    def assert_response_format(self, response, expected_status=None):
        """Assert response follows DRF Commons format."""
        if expected_status:
            self.assertEqual(response.status_code, expected_status)

        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        self.assertIn("success", response.data)

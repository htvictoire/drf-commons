"""
Base test case classes for DRF Common library tests.
"""

from unittest.mock import Mock

from django.test import TestCase, TransactionTestCase

from rest_framework.test import APITestCase

from drf_common.current_user.utils import _thread_locals
from .utils import mock_current_user


class DrfCommonTestCase(TestCase):
    """Base test case for DRF Common tests."""

    def setUp(self):
        super().setUp()
        self.addCleanup(self._cleanup_thread_locals)

    def _cleanup_thread_locals(self):
        """Clean up thread-local variables after test."""
        if hasattr(_thread_locals, "_current_user"):
            delattr(_thread_locals, "_current_user")


class DrfCommonTransactionTestCase(TransactionTestCase):
    """Base transaction test case for DRF Common tests."""

    def setUp(self):
        super().setUp()
        self.addCleanup(self._cleanup_thread_locals)

    def _cleanup_thread_locals(self):
        """Clean up thread-local variables after test."""
        if hasattr(_thread_locals, "_current_user"):
            delattr(_thread_locals, "_current_user")


class DrfCommonAPITestCase(APITestCase):
    """Base API test case for DRF Common API tests."""

    def setUp(self):
        super().setUp()
        self.addCleanup(self._cleanup_thread_locals)

    def _cleanup_thread_locals(self):
        """Clean up thread-local variables after test."""
        if hasattr(_thread_locals, "_current_user"):
            delattr(_thread_locals, "_current_user")


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
        """Assert response follows DRF Common format."""
        if expected_status:
            self.assertEqual(response.status_code, expected_status)

        self.assertIn("data", response.data)
        self.assertIn("message", response.data)
        self.assertIn("success", response.data)

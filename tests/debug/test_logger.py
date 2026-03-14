"""
Tests for StructuredLogger class.
"""

from unittest.mock import Mock

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.common_tests.utils import capture_logs, override_debug_settings

from drf_commons.debug.logger import StructuredLogger


class TestStructuredLogger(DrfCommonTestCase):
    """Test StructuredLogger functionality."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_init_with_category(self):
        """StructuredLogger initializes with name and category."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["users"]
        ):
            logger = StructuredLogger("test.logger", "users")
            self.assertEqual(logger.name, "test.logger")
            self.assertEqual(logger.category, "users")

    def test_log_user_action_with_resource(self):
        """log_user_action logs user action with resource."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["users"]
        ):
            logger = StructuredLogger("test.logger", "users")

            with capture_logs("test.logger") as log_output:
                logger.log_user_action(self.user, "created", "Article", "title updated")

                expected = f"User {self.user.username} (ID: {self.user.id}) performed created on Article - Details: title updated"
                self.assertIn(expected, log_output.getvalue())

    def test_log_user_action_without_resource(self):
        """log_user_action logs user action without resource."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["users"]
        ):
            logger = StructuredLogger("test.logger", "users")

            with capture_logs("test.logger") as log_output:
                logger.log_user_action(self.user, "login")

                expected = (
                    f"User {self.user.username} (ID: {self.user.id}) performed login"
                )
                self.assertIn(expected, log_output.getvalue())

    def test_log_user_action_anonymous(self):
        """log_user_action handles anonymous user."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["users"]
        ):
            logger = StructuredLogger("test.logger", "users")
            mock_user = Mock()
            mock_user.id = None
            mock_user.username = None
            mock_user.is_authenticated = False

            with capture_logs("test.logger") as log_output:
                logger.log_user_action(mock_user, "viewed")

                expected = "User anonymous (ID: anonymous) performed viewed"
                self.assertIn(expected, log_output.getvalue())

    def test_log_api_request_authenticated(self):
        """log_api_request logs authenticated request."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["api"]
        ):
            logger = StructuredLogger("test.logger", "api")
            mock_request = Mock()
            mock_request.method = "GET"
            mock_request.path = "/api/users/"
            mock_request.user = self.user

            mock_response = Mock()
            mock_response.status_code = 200

            with capture_logs("test.logger") as log_output:
                logger.log_api_request(mock_request, mock_response, 0.1234)

                expected = f"GET /api/users/ by {self.user.username} - Status: 200 - Duration: 0.1234s"
                self.assertIn(expected, log_output.getvalue())

    def test_log_api_request_unauthenticated(self):
        """log_api_request logs unauthenticated request."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["api"]
        ):
            logger = StructuredLogger("test.logger", "api")
            mock_request = Mock()
            mock_request.method = "POST"
            mock_request.path = "/api/login/"
            mock_request.user.is_authenticated = False

            with capture_logs("test.logger") as log_output:
                logger.log_api_request(mock_request)

                expected = "POST /api/login/"
                self.assertIn(expected, log_output.getvalue())
                self.assertNotIn("by ", log_output.getvalue())

    def test_log_error_with_context(self):
        """log_error logs error with context information."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors"]
        ):
            logger = StructuredLogger("test.logger", "errors")
            error = ValueError("test error")

            with capture_logs("test.logger") as log_output:
                logger.log_error(error, {"user_id": self.user.id})

                self.assertIn("Error: test error", log_output.getvalue())
                self.assertIn(
                    f"Context: {{'user_id': {self.user.id}}}", log_output.getvalue()
                )

    def test_log_error_without_context(self):
        """log_error logs error without context."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors"]
        ):
            logger = StructuredLogger("test.logger", "errors")
            error = ValueError("test error")

            with capture_logs("test.logger") as log_output:
                logger.log_error(error)

                self.assertIn("Error: test error", log_output.getvalue())
                self.assertNotIn("Context:", log_output.getvalue())

    def test_log_performance_with_details(self):
        """log_performance logs performance metrics with details."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["performance"]
        ):
            logger = StructuredLogger("test.logger", "performance")

            with capture_logs("test.logger") as log_output:
                logger.log_performance("database query", 0.0456, "15 records fetched")

                expected = (
                    "Performance: database query took 0.0456s - 15 records fetched"
                )
                self.assertIn(expected, log_output.getvalue())

    def test_log_performance_without_details(self):
        """log_performance logs performance metrics without details."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["performance"]
        ):
            logger = StructuredLogger("test.logger", "performance")

            with capture_logs("test.logger") as log_output:
                logger.log_performance("cache lookup", 0.0123)

                expected = "Performance: cache lookup took 0.0123s"
                self.assertIn(expected, log_output.getvalue())
                self.assertNotIn(" - ", log_output.getvalue())

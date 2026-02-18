"""
Tests for logging decorators.
"""

import json
from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.test import RequestFactory

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.debug.core.categories import Categories

from ..logging import api_request_logger, log_exceptions, log_function_call


class ApiRequestLoggerTests(DrfCommonTestCase):
    """Tests for api_request_logger decorator."""

    def setUp(self):
        """Set up test dependencies."""
        super().setUp()
        self.factory = RequestFactory()

    @patch("decorators.logging.Categories")
    def test_basic_api_logging(self, mock_categories):
        """Test basic API request logging without body or headers."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        @api_request_logger()
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.get("/test-endpoint/?param=value")
        response = test_view(request)

        # Verify logger was created with correct name and category
        mock_categories.get_logger.assert_called_with(
            "api.test_view", mock_categories.API
        )

        # Verify basic logging calls
        mock_logger.info.assert_any_call("API GET /test-endpoint/")
        mock_logger.debug.assert_any_call("Query params: {'param': ['value']}")
        mock_logger.info.assert_any_call("API GET /test-endpoint/ - Status: 200")

        self.assertEqual(response.content, b"OK")

    @patch("decorators.logging.Categories")
    def test_api_logging_with_headers(self, mock_categories):
        """Test API logging with headers enabled."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        @api_request_logger(log_headers=True)
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.get(
            "/test-endpoint/", HTTP_AUTHORIZATION="Bearer token123"
        )
        test_view(request)

        # Verify headers were logged
        headers_call_made = any(
            "Headers:" in str(call) for call in mock_logger.debug.call_args_list
        )
        self.assertTrue(headers_call_made)

    @patch("decorators.logging.Categories")
    def test_api_logging_with_body(self, mock_categories):
        """Test API logging with request body enabled."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        @api_request_logger(log_body=True)
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.post(
            "/test-endpoint/", data='{"test": "data"}', content_type="application/json"
        )
        test_view(request)

        # Verify body was attempted to be logged
        body_call_made = any(
            "Request body:" in str(call) for call in mock_logger.debug.call_args_list
        )
        self.assertTrue(body_call_made)

    @patch("decorators.logging.Categories")
    def test_api_logging_binary_body(self, mock_categories):
        """Test API logging with binary request body."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        @api_request_logger(log_body=True)
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.post(
            "/test-endpoint/",
            data=b"\x80\x81\x82\xff",  # Invalid UTF-8 bytes
            content_type="application/octet-stream",
        )
        test_view(request)

        # Should log binary data message
        body_call_made = any(
            "binary data" in str(call) for call in mock_logger.debug.call_args_list
        )
        self.assertTrue(body_call_made)

    @patch("drf_commons.decorators.logging.Categories")
    def test_api_logging_redacts_sensitive_headers(self, mock_categories):
        """Sensitive headers should be redacted before logging."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        @api_request_logger(log_headers=True)
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.get(
            "/test-endpoint/",
            HTTP_AUTHORIZATION="Bearer secret-token",
            HTTP_X_API_KEY="abc123",
            HTTP_ACCEPT="application/json",
        )
        test_view(request)

        headers_log_lines = [
            call.args[0]
            for call in mock_logger.debug.call_args_list
            if call.args and call.args[0].startswith("Headers:")
        ]
        self.assertEqual(len(headers_log_lines), 1)
        headers_log = headers_log_lines[0]
        self.assertIn("***REDACTED***", headers_log)
        self.assertNotIn("secret-token", headers_log)
        self.assertNotIn("abc123", headers_log)

    @patch("drf_commons.decorators.logging.Categories")
    def test_api_logging_redacts_and_truncates_json_body(self, mock_categories):
        """JSON body logging should redact sensitive fields and truncate payload."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        @api_request_logger(log_body=True, max_body_length=80)
        def test_view(request):
            return HttpResponse("OK")

        payload = {
            "username": "alice",
            "password": "super-secret-password",
            "profile": {"token": "nested-secret-token"},
            "notes": "x" * 400,
        }
        request = self.factory.post(
            "/test-endpoint/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        test_view(request)

        body_log_lines = [
            call.args[0]
            for call in mock_logger.debug.call_args_list
            if call.args and call.args[0].startswith("Request body:")
        ]
        self.assertEqual(len(body_log_lines), 1)
        body_log = body_log_lines[0]
        self.assertIn("***REDACTED***", body_log)
        self.assertIn("<truncated", body_log)
        self.assertNotIn("super-secret-password", body_log)
        self.assertNotIn("nested-secret-token", body_log)

    @patch("drf_commons.decorators.logging.Categories")
    def test_api_logging_supports_custom_sanitizer_hook(self, mock_categories):
        """Custom sanitizer hook should override sanitized payloads."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        def sanitizer_hook(request, headers, body):
            return {"headers": {"X-Trace": "custom"}, "body": "<custom-body>"}

        @api_request_logger(
            log_headers=True, log_body=True, sanitizer_hook=sanitizer_hook
        )
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.post(
            "/test-endpoint/",
            data=json.dumps({"password": "secret"}),
            content_type="application/json",
            HTTP_AUTHORIZATION="Bearer token",
        )
        test_view(request)

        mock_logger.debug.assert_any_call("Headers: {'X-Trace': 'custom'}")
        mock_logger.debug.assert_any_call("Request body: <custom-body>")


class LogFunctionCallTests(DrfCommonTestCase):
    """Tests for log_function_call decorator."""

    @patch("decorators.logging.Categories")
    @patch("decorators.logging.time")
    def test_function_call_logging_basic(self, mock_time, mock_categories):
        """Test basic function call logging."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.5]  # 0.5s execution

        @log_function_call()
        def test_function(arg1, arg2, kwarg1=None):
            return "result"

        result = test_function("value1", "value2", kwarg1="kwvalue")

        # Verify logger was created
        mock_categories.get_logger.assert_called_with(
            f"{test_function.__module__}.test_function", Categories.PERFORMANCE
        )

        # Verify logging calls
        mock_logger.debug.assert_any_call(
            "Calling test_function with args=('value1', 'value2'), kwargs={'kwarg1': 'kwvalue'}"
        )
        mock_logger.debug.assert_any_call(
            "test_function completed in 0.5000s, result=result"
        )

        self.assertEqual(result, "result")

    @patch("decorators.logging.Categories")
    @patch("decorators.logging.time")
    def test_function_call_logging_no_args_result(self, mock_time, mock_categories):
        """Test function call logging without args and result."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.2]

        @log_function_call(log_args=False, log_result=False)
        def test_function():
            return "result"

        test_function()

        # Verify basic logging without args/result
        mock_logger.debug.assert_any_call("Calling test_function")
        mock_logger.debug.assert_any_call("test_function completed in 0.2000s")

    @patch("decorators.logging.Categories")
    @patch("decorators.logging.time")
    def test_function_call_logging_exception(self, mock_time, mock_categories):
        """Test function call logging with exception."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.3]

        @log_function_call()
        def test_function():
            raise ValueError("Test error")

        with self.assertRaises(ValueError):
            test_function()

        # Verify exception logging
        mock_logger.error.assert_called_with(
            "test_function failed after 0.3000s with error: Test error"
        )

    @patch("decorators.logging.Categories")
    def test_custom_logger_name(self, mock_categories):
        """Test function call logging with custom logger name."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        @log_function_call(logger_name="custom.logger")
        def test_function():
            return "result"

        test_function()

        # Verify custom logger name was used
        mock_categories.get_logger.assert_called_with(
            "custom.logger", Categories.PERFORMANCE
        )


class LogExceptionsTests(DrfCommonTestCase):
    """Tests for log_exceptions decorator."""

    @patch("decorators.logging.Categories")
    def test_exception_logging_with_reraise(self, mock_categories):
        """Test exception logging with reraise enabled."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        @log_exceptions()
        def test_function(arg1, arg2):
            raise ValueError("Test error")

        with self.assertRaises(ValueError):
            test_function("value1", "value2")

        # Verify exception was logged with details
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args

        self.assertIn("Exception in test_function: Test error", call_args[0][0])
        self.assertTrue(call_args[1]["exc_info"])
        self.assertEqual(call_args[1]["extra"]["function"], "test_function")
        self.assertEqual(call_args[1]["extra"]["exception_type"], "ValueError")

    @patch("decorators.logging.Categories")
    def test_exception_logging_no_reraise(self, mock_categories):
        """Test exception logging without reraise."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        @log_exceptions(reraise=False)
        def test_function():
            raise ValueError("Test error")

        result = test_function()

        # Should return None and not reraise
        self.assertIsNone(result)
        mock_logger.error.assert_called_once()

    @patch("decorators.logging.Categories")
    def test_exception_logging_success(self, mock_categories):
        """Test that successful function calls don't trigger exception logging."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        @log_exceptions()
        def test_function():
            return "success"

        result = test_function()

        self.assertEqual(result, "success")
        mock_logger.error.assert_not_called()

    @patch("decorators.logging.Categories")
    def test_custom_exception_logger_name(self, mock_categories):
        """Test exception logging with custom logger name."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        @log_exceptions(logger_name="custom.error.logger", reraise=False)
        def test_function():
            raise RuntimeError("Test error")

        test_function()

        # Verify custom logger name was used
        mock_categories.get_logger.assert_called_with(
            "custom.error.logger", mock_categories.ERRORS
        )

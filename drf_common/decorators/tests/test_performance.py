"""
Tests for performance decorators.
"""

from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.test import RequestFactory

from drf_common.common_tests.base_cases import DrfCommonTestCase

from ..performance import api_performance_monitor


class ApiPerformanceMonitorTests(DrfCommonTestCase):
    """Tests for api_performance_monitor decorator."""

    def setUp(self):
        """Set up test dependencies."""
        super().setUp()
        self.factory = RequestFactory()

    @patch("decorators.performance.Categories")
    @patch("decorators.performance.time")
    def test_fast_api_performance_monitoring(self, mock_time, mock_categories):
        """Test performance monitoring for fast API calls."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [
            1000.0,
            1000.5,
        ]  # 0.5s execution (under threshold)

        @api_performance_monitor(threshold=1.0)
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.get("/test-endpoint/")
        response = test_view(request)

        # Verify logger was created with correct name and category
        mock_categories.get_logger.assert_called_with(
            "performance.test_view", mock_categories.PERFORMANCE
        )

        # Should log info for fast request
        mock_logger.info.assert_called_with("API timing: GET /test-endpoint/ - 0.5000s")
        mock_logger.warning.assert_not_called()

        self.assertEqual(response.content, b"OK")

    @patch("decorators.performance.Categories")
    @patch("decorators.performance.time")
    def test_slow_api_performance_monitoring(self, mock_time, mock_categories):
        """Test performance monitoring for slow API calls."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1001.5]  # 1.5s execution (over threshold)

        @api_performance_monitor(threshold=1.0)
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.post("/slow-endpoint/")
        response = test_view(request)

        # Should log warning for slow request
        mock_logger.warning.assert_called_with(
            "Slow API: POST /slow-endpoint/ - 1.5000s"
        )
        mock_logger.info.assert_not_called()

        self.assertEqual(response.content, b"OK")

    @patch("decorators.performance.Categories")
    @patch("decorators.performance.time")
    def test_api_performance_monitoring_with_exception(
        self, mock_time, mock_categories
    ):
        """Test performance monitoring when API raises exception."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.8]  # 0.8s execution before exception

        @api_performance_monitor(threshold=1.0)
        def test_view(request):
            raise ValueError("Test error")

        request = self.factory.get("/error-endpoint/")

        with self.assertRaises(ValueError):
            test_view(request)

        # Should log error with timing information
        mock_logger.error.assert_called_with(
            "API failed: GET /error-endpoint/ - 0.8000s: Test error"
        )
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()

    @patch("decorators.performance.Categories")
    @patch("decorators.performance.time")
    def test_custom_threshold(self, mock_time, mock_categories):
        """Test performance monitoring with custom threshold."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.3]  # 0.3s execution

        @api_performance_monitor(threshold=0.2)  # Lower threshold
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.get("/test-endpoint/")
        test_view(request)

        # Should log warning because 0.3s > 0.2s threshold
        mock_logger.warning.assert_called_with(
            "Slow API: GET /test-endpoint/ - 0.3000s"
        )
        mock_logger.info.assert_not_called()

    @patch("decorators.performance.Categories")
    @patch("decorators.performance.time")
    def test_default_threshold(self, mock_time, mock_categories):
        """Test performance monitoring with default threshold."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1001.2]  # 1.2s execution

        @api_performance_monitor()  # Default threshold is 1.0
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.get("/test-endpoint/")
        test_view(request)

        # Should log warning because 1.2s > 1.0s default threshold
        mock_logger.warning.assert_called_with(
            "Slow API: GET /test-endpoint/ - 1.2000s"
        )

    @patch("decorators.performance.Categories")
    @patch("decorators.performance.time")
    def test_performance_monitoring_preserves_response(
        self, mock_time, mock_categories
    ):
        """Test that performance monitoring preserves original response."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.1]

        @api_performance_monitor()
        def test_view(request):
            response = HttpResponse("Custom content")
            response.status_code = 201
            response["Custom-Header"] = "value"
            return response

        request = self.factory.post("/test-endpoint/")
        response = test_view(request)

        # Response should be preserved exactly
        self.assertEqual(response.content, b"Custom content")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response["Custom-Header"], "value")

    @patch("decorators.performance.Categories")
    @patch("decorators.performance.time")
    def test_performance_monitoring_with_query_parameters(
        self, mock_time, mock_categories
    ):
        """Test performance monitoring logs correct path with query parameters."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.side_effect = [1000.0, 1000.1]

        @api_performance_monitor()
        def test_view(request):
            return HttpResponse("OK")

        request = self.factory.get("/test-endpoint/?param1=value1&param2=value2")
        test_view(request)

        # Should log the correct path (without query parameters)
        mock_logger.info.assert_called_with("API timing: GET /test-endpoint/ - 0.1000s")

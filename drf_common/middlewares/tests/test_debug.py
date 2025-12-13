"""
Tests for debug middlewares.
"""

from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.test import RequestFactory

from drf_common.common_tests.base_cases import DrfCommonTestCase
from drf_common.common_tests.factories import UserFactory

from ..debug import DebugMiddleware, ProfilerMiddleware, SQLDebugMiddleware


class DebugMiddlewareTests(DrfCommonTestCase):
    """Tests for DebugMiddleware."""

    def setUp(self):
        """Set up test dependencies."""
        super().setUp()
        self.factory = RequestFactory()

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.connection")
    @patch("middlewares.debug.time")
    def test_middleware_initialization(
        self, mock_time, mock_connection, mock_categories
    ):
        """Test middleware initialization."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        get_response = Mock()
        middleware = DebugMiddleware(get_response)

        mock_categories.get_logger.assert_called_with(
            "middleware.debug", mock_categories.REQUESTS
        )
        self.assertEqual(middleware.logger, mock_logger)

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.connection")
    @patch("middlewares.debug.time")
    def test_process_request(self, mock_time, mock_connection, mock_categories):
        """Test request processing."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.return_value = 1000.0
        mock_connection.queries = ["query1", "query2"]

        get_response = Mock()
        middleware = DebugMiddleware(get_response)

        user = UserFactory()
        request = self.factory.get("/test-path/?param=value")
        request.user = user
        request.META["HTTP_USER_AGENT"] = "Test Agent"
        request.META["REMOTE_ADDR"] = "192.168.1.1"

        result = middleware.process_request(request)

        # Should return None
        self.assertIsNone(result)

        # Should set debug attributes
        self.assertEqual(request._debug_start_time, 1000.0)
        self.assertEqual(request._debug_initial_queries, 2)

        # Should log request details
        mock_logger.info.assert_called_with("Request started: GET /test-path/")
        mock_logger.debug.assert_any_call(f"User: {user.username}")
        mock_logger.debug.assert_any_call("User Agent: Test Agent")
        mock_logger.debug.assert_any_call("Remote IP: 192.168.1.1")
        mock_logger.debug.assert_any_call("Query params: {'param': ['value']}")

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.connection")
    @patch("middlewares.debug.time")
    @patch("middlewares.debug.settings")
    def test_process_response_normal(
        self, mock_settings, mock_time, mock_connection, mock_categories
    ):
        """Test normal response processing."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_categories._null_logger = Mock()
        mock_time.time.return_value = 1000.5  # 0.5s after request start
        mock_connection.queries = ["q1", "q2", "q3", "q4", "q5"]  # 3 new queries
        mock_settings.DEBUG_SLOW_REQUEST_THRESHOLD = 1.0
        mock_settings.DEBUG_HIGH_QUERY_COUNT_THRESHOLD = 5

        get_response = Mock()
        middleware = DebugMiddleware(get_response)

        request = self.factory.get("/test-path/")
        request._debug_start_time = 1000.0
        request._debug_initial_queries = 2

        response = HttpResponse("OK")
        response.status_code = 200

        result = middleware.process_response(request, response)

        # Should return the response
        self.assertEqual(result, response)

        # Should log completion
        mock_logger.info.assert_called_with(
            "Request completed: GET /test-path/ - Status: 200 - Duration: 0.5000s - Queries: 3"
        )

        # Should not warn (under thresholds)
        mock_logger.warning.assert_not_called()

        # Should add debug headers
        self.assertEqual(response["X-Debug-Duration"], "0.5000s")
        self.assertEqual(response["X-Debug-Queries"], "3")

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.connection")
    @patch("middlewares.debug.time")
    @patch("middlewares.debug.settings")
    def test_process_response_slow_request(
        self, mock_settings, mock_time, mock_connection, mock_categories
    ):
        """Test response processing for slow request."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_categories._null_logger = Mock()
        mock_time.time.return_value = 1001.5  # 1.5s after request start
        mock_connection.queries = ["q1", "q2"]
        mock_settings.DEBUG_SLOW_REQUEST_THRESHOLD = 1.0
        mock_settings.DEBUG_HIGH_QUERY_COUNT_THRESHOLD = 5

        get_response = Mock()
        middleware = DebugMiddleware(get_response)

        request = self.factory.get("/test-path/")
        request._debug_start_time = 1000.0
        request._debug_initial_queries = 2

        response = HttpResponse("OK")
        middleware.process_response(request, response)

        # Should warn about slow request
        mock_logger.warning.assert_any_call(
            "Slow request detected: 1.5000s for /test-path/"
        )

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.connection")
    @patch("middlewares.debug.time")
    @patch("middlewares.debug.settings")
    def test_process_response_high_query_count(
        self, mock_settings, mock_time, mock_connection, mock_categories
    ):
        """Test response processing for high query count."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_categories._null_logger = Mock()
        mock_time.time.return_value = 1000.5
        mock_connection.queries = [
            "q1",
            "q2",
            "q3",
            "q4",
            "q5",
            "q6",
            "q7",
            "q8",
        ]  # 6 new queries
        mock_settings.DEBUG_SLOW_REQUEST_THRESHOLD = 1.0
        mock_settings.DEBUG_HIGH_QUERY_COUNT_THRESHOLD = 5

        get_response = Mock()
        middleware = DebugMiddleware(get_response)

        request = self.factory.get("/test-path/")
        request._debug_start_time = 1000.0
        request._debug_initial_queries = 2

        response = HttpResponse("OK")
        middleware.process_response(request, response)

        # Should warn about high query count
        mock_logger.warning.assert_any_call(
            "High query count: 6 queries for /test-path/"
        )

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.time")
    def test_process_exception(self, mock_time, mock_categories):
        """Test exception processing."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_time.time.return_value = 1000.8

        get_response = Mock()
        middleware = DebugMiddleware(get_response)

        request = self.factory.get("/test-path/")
        request._debug_start_time = 1000.0
        exception = ValueError("Test exception")

        result = middleware.process_exception(request, exception)

        # Should return None (don't handle exception)
        self.assertIsNone(result)

        # Should log error
        mock_logger.error.assert_called_with(
            "Request failed: GET /test-path/ - Duration: 0.8000s - Exception: Test exception",
            exc_info=True,
        )

    def test_get_client_ip_with_forwarded(self):
        """Test client IP extraction with X-Forwarded-For header."""
        get_response = Mock()
        middleware = DebugMiddleware(get_response)

        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1, 192.168.1.1"
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        ip = middleware.get_client_ip(request)
        self.assertEqual(ip, "10.0.0.1")

    def test_get_client_ip_without_forwarded(self):
        """Test client IP extraction without X-Forwarded-For header."""
        get_response = Mock()
        middleware = DebugMiddleware(get_response)

        request = self.factory.get("/")
        request.META["REMOTE_ADDR"] = "192.168.1.100"

        ip = middleware.get_client_ip(request)
        self.assertEqual(ip, "192.168.1.100")


class SQLDebugMiddlewareTests(DrfCommonTestCase):
    """Tests for SQLDebugMiddleware."""

    def setUp(self):
        """Set up test dependencies."""
        super().setUp()
        self.factory = RequestFactory()

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.connection")
    def test_middleware_initialization(self, mock_connection, mock_categories):
        """Test SQL middleware initialization."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger

        get_response = Mock()
        middleware = SQLDebugMiddleware(get_response)

        mock_categories.get_logger.assert_called_with(
            "middleware.sql", mock_categories.DATABASE
        )
        self.assertEqual(middleware.logger, mock_logger)

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.connection")
    def test_process_request(self, mock_connection, mock_categories):
        """Test SQL request processing."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_connection.queries = ["q1", "q2", "q3"]

        get_response = Mock()
        middleware = SQLDebugMiddleware(get_response)

        request = self.factory.get("/test-path/")
        result = middleware.process_request(request)

        self.assertIsNone(result)
        self.assertEqual(request._sql_debug_initial_queries, 3)

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.connection")
    @patch("middlewares.debug.settings")
    def test_process_response_with_queries(
        self, mock_settings, mock_connection, mock_categories
    ):
        """Test SQL response processing with queries."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_settings.DEBUG_SLOW_QUERY_THRESHOLD = 0.1

        # Mock connection queries with new queries added
        existing_queries = [
            {"sql": "SELECT 1", "time": "0.001"},
            {"sql": "SELECT 2", "time": "0.002"},
        ]
        new_queries = [
            {"sql": "SELECT * FROM users", "time": "0.050"},
            {"sql": "UPDATE users SET name = %s", "time": "0.150"},  # Slow query
        ]
        mock_connection.queries = existing_queries + new_queries

        get_response = Mock()
        middleware = SQLDebugMiddleware(get_response)

        request = self.factory.get("/test-path/")
        request._sql_debug_initial_queries = 2

        response = HttpResponse("OK")
        result = middleware.process_response(request, response)

        self.assertEqual(result, response)

        # Should log query summary
        mock_logger.info.assert_called_with(
            "SQL queries for /test-path/: 2 queries, total time: 0.2000s"
        )

        # Should log individual queries
        mock_logger.debug.assert_any_call("Query 1: SELECT * FROM users (Time: 0.050s)")
        mock_logger.debug.assert_any_call(
            "Query 2: UPDATE users SET name = %s (Time: 0.150s)"
        )

        # Should warn about slow queries
        mock_logger.warning.assert_called_with(
            "Slow queries detected: 1 queries > 0.1s"
        )

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.connection")
    def test_process_response_no_queries(self, mock_connection, mock_categories):
        """Test SQL response processing with no new queries."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_connection.queries = ["q1", "q2"]

        get_response = Mock()
        middleware = SQLDebugMiddleware(get_response)

        request = self.factory.get("/test-path/")
        request._sql_debug_initial_queries = 2

        response = HttpResponse("OK")
        result = middleware.process_response(request, response)

        self.assertEqual(result, response)

        # Should not log anything for no queries
        mock_logger.info.assert_not_called()
        mock_logger.debug.assert_not_called()
        mock_logger.warning.assert_not_called()


class ProfilerMiddlewareTests(DrfCommonTestCase):
    """Tests for ProfilerMiddleware."""

    def setUp(self):
        """Set up test dependencies."""
        super().setUp()
        self.factory = RequestFactory()

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.settings")
    def test_middleware_initialization_enabled(self, mock_settings, mock_categories):
        """Test profiler middleware initialization when enabled."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_categories._null_logger = Mock()
        mock_settings.ENABLE_PROFILER = True

        get_response = Mock()
        middleware = ProfilerMiddleware(get_response)

        mock_categories.get_logger.assert_called_with(
            "middleware.profiler", mock_categories.PERFORMANCE
        )
        self.assertEqual(middleware.logger, mock_logger)
        self.assertTrue(middleware.enabled)

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.settings")
    def test_middleware_initialization_disabled(self, mock_settings, mock_categories):
        """Test profiler middleware initialization when disabled."""
        mock_categories.get_logger.return_value = mock_categories._null_logger
        mock_settings.ENABLE_PROFILER = False

        get_response = Mock()
        middleware = ProfilerMiddleware(get_response)

        self.assertFalse(middleware.enabled)

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.settings")
    def test_process_request_disabled(self, mock_settings, mock_categories):
        """Test profiler request processing when disabled."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_categories._null_logger = Mock()
        mock_settings.ENABLE_PROFILER = False

        get_response = Mock()
        middleware = ProfilerMiddleware(get_response)
        middleware.enabled = False

        request = self.factory.get("/test-path/")
        result = middleware.process_request(request)

        self.assertIsNone(result)
        self.assertFalse(hasattr(request, "_profiler"))

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.settings")
    def test_process_request_enabled(self, mock_settings, mock_categories):
        """Test profiler request processing when enabled."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_categories._null_logger = Mock()
        mock_settings.ENABLE_PROFILER = True

        get_response = Mock()
        middleware = ProfilerMiddleware(get_response)
        middleware.enabled = True

        request = self.factory.get("/test-path/")

        with patch("middlewares.debug.cProfile") as mock_cprofile:
            mock_profiler = Mock()
            mock_cprofile.Profile.return_value = mock_profiler

            result = middleware.process_request(request)

            self.assertIsNone(result)
            self.assertEqual(request._profiler, mock_profiler)
            mock_profiler.enable.assert_called_once()


    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.settings")
    def test_process_response_enabled(self, mock_settings, mock_categories):
        """Test profiler response processing when enabled."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_categories._null_logger = Mock()
        mock_settings.ENABLE_PROFILER = True
        mock_settings.DEBUG_PROFILER_SORT_METHOD = "cumulative"
        mock_settings.DEBUG_PROFILER_TOP_FUNCTIONS = 10

        get_response = Mock()
        middleware = ProfilerMiddleware(get_response)
        middleware.enabled = True

        request = self.factory.get("/test-path/")
        mock_profiler = Mock()
        request._profiler = mock_profiler

        response = HttpResponse("OK")

        with patch("middlewares.debug.io") as mock_io, patch(
            "middlewares.debug.pstats"
        ) as mock_pstats:

            mock_stringio = Mock()
            mock_io.StringIO.return_value = mock_stringio
            mock_stringio.getvalue.return_value = "Profiling data here"

            mock_stats = Mock()
            mock_pstats.Stats.return_value = mock_stats

            result = middleware.process_response(request, response)

            self.assertEqual(result, response)
            mock_profiler.disable.assert_called_once()
            mock_pstats.Stats.assert_called_with(mock_profiler, stream=mock_stringio)
            mock_stats.sort_stats.assert_called_with("cumulative")
            mock_stats.print_stats.assert_called_with(10)

            mock_logger.info.assert_any_call("Profiling results for /test-path/:")
            mock_logger.info.assert_any_call("Profiling data here")

    @patch("middlewares.debug.Categories")
    @patch("middlewares.debug.settings")
    def test_process_response_disabled(self, mock_settings, mock_categories):
        """Test profiler response processing when disabled."""
        mock_logger = Mock()
        mock_categories.get_logger.return_value = mock_logger
        mock_categories._null_logger = Mock()
        mock_settings.ENABLE_PROFILER = False

        get_response = Mock()
        middleware = ProfilerMiddleware(get_response)
        middleware.enabled = False

        request = self.factory.get("/test-path/")
        response = HttpResponse("OK")

        result = middleware.process_response(request, response)

        self.assertEqual(result, response)
        mock_logger.info.assert_not_called()

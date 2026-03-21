"""
Tests for debug utility functions.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.common_tests.utils import capture_logs, override_debug_settings

from drf_commons.debug.core.categories import Categories
from drf_commons.debug.utils import (
    analyze_queryset,
    capture_request_data,
    debug_cache_operations,
    debug_context_processor,
    debug_print,
    debug_sql_queries,
    format_traceback,
    log_model_changes,
    memory_usage,
    pretty_print_dict,
    profile_function,
)


class TestDebugPrint(DrfCommonTestCase):
    """Test debug_print function."""

    @patch("builtins.print")
    def test_debug_print_enabled_category(self, mock_print):
        """debug_print outputs when category is enabled."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors"]
        ):
            debug_print("test message", category="errors")
            mock_print.assert_called_once_with("[DEBUG]", "test message")

    @patch("builtins.print")
    def test_debug_print_disabled_category(self, mock_print):
        """debug_print does not output when category is disabled."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=[]
        ):
            debug_print("test message", category="errors")
            mock_print.assert_not_called()

    @patch("builtins.print")
    def test_debug_print_with_kwargs(self, mock_print):
        """debug_print passes kwargs to print function."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors"]
        ):
            debug_print("test", "message", category="errors", sep="-")
            mock_print.assert_called_once_with("[DEBUG]", "test", "message", sep="-")


class TestPrettyPrintDict(DrfCommonTestCase):
    """Test pretty_print_dict function."""

    @patch("builtins.print")
    @patch("pprint.pprint")
    def test_pretty_print_dict_with_title(self, mock_pprint, mock_print):
        """pretty_print_dict outputs dictionary with title."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors"]
        ):
            test_dict = {"key": "value"}
            pretty_print_dict(test_dict, title="Test Data", category="errors")

            mock_print.assert_any_call("\n=== Test Data ===")
            mock_pprint.assert_called_once_with(test_dict, indent=2, width=120)

    @patch("builtins.print")
    def test_pretty_print_dict_disabled_category(self, mock_print):
        """pretty_print_dict does nothing when category is disabled."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=[]
        ):
            pretty_print_dict({"key": "value"}, category="errors")
            mock_print.assert_not_called()

    @patch("builtins.print")
    @patch("pprint.pprint")
    def test_pretty_print_object_with_dict(self, mock_pprint, mock_print):
        """pretty_print_dict handles objects with __dict__."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors"]
        ):
            test_obj = Mock()
            test_obj.__dict__ = {"attr": "value"}

            pretty_print_dict(test_obj, category="errors")
            mock_pprint.assert_called_once_with({"attr": "value"}, indent=2, width=120)

    @patch("builtins.print")
    @patch("pprint.pprint")
    def test_pretty_print_plain_object_without_dict(self, mock_pprint, mock_print):
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors"]
        ):
            pretty_print_dict(123, category="errors")

            mock_pprint.assert_called_once_with(123, indent=2, width=120)

    @patch("builtins.print")
    @patch("pprint.pprint", side_effect=RuntimeError("boom"))
    def test_pretty_print_falls_back_to_string_on_error(self, mock_pprint, mock_print):
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors"]
        ):
            pretty_print_dict(123, category="errors")

            mock_print.assert_called_once_with("123")


class TestDebugSqlQueries(DrfCommonTestCase):
    """Test debug_sql_queries function."""

    @patch("builtins.print")
    @patch("drf_commons.debug.utils.connection")
    def test_debug_sql_queries_enabled(self, mock_connection, mock_print):
        """debug_sql_queries outputs when database category is enabled."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["database"]
        ):
            # Mock connection.queries
            mock_queries = [
                {"sql": "SELECT * FROM users", "time": "0.1234"},
                {"sql": "SELECT * FROM posts", "time": "0.0567"},
            ]
            mock_connection.queries = mock_queries

            debug_sql_queries()

            # Check that queries were printed
            mock_print.assert_any_call("\n=== SQL Queries (2 total) ===")
            mock_print.assert_any_call("\nQuery 1 (0.1234s):")
            mock_print.assert_any_call("SELECT * FROM users")

    @patch("builtins.print")
    def test_debug_sql_queries_disabled(self, mock_print):
        """debug_sql_queries does nothing when database category is disabled."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=[]
        ):
            debug_sql_queries()
            mock_print.assert_not_called()

    @patch("builtins.print")
    @patch("drf_commons.debug.utils.connection")
    def test_debug_sql_queries_can_reset_query_log(self, mock_connection, mock_print):
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["database"]
        ):
            mock_connection.queries = [{"sql": "SELECT 1", "time": "0.1000"}]

            debug_sql_queries(reset=True)

            mock_connection.queries_log.clear.assert_called_once_with()


class TestCaptureRequestData(DrfCommonTestCase):
    """Test capture_request_data function."""

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.user = UserFactory()

    def test_capture_get_request_data(self):
        """capture_request_data captures GET request data."""
        request = self.factory.get("/api/users/?page=1", HTTP_USER_AGENT="test-agent")
        request.user = self.user

        data = capture_request_data(request)

        self.assertEqual(data["method"], "GET")
        self.assertEqual(data["path"], "/api/users/")
        self.assertEqual(data["user"], str(self.user))
        self.assertEqual(data["query_params"], {"page": ["1"]})
        self.assertEqual(data["headers"]["user_agent"], "test-agent")

    def test_capture_post_request_data(self):
        """capture_request_data captures POST request data."""
        request = self.factory.post("/api/users/", {"name": "test"})
        request.user = self.user

        data = capture_request_data(request)

        self.assertEqual(data["method"], "POST")
        self.assertEqual(data["post_data"], {"name": ["test"]})

    def test_capture_request_filters_sensitive_headers(self):
        """capture_request_data filters sensitive headers."""
        request = self.factory.get(
            "/api/users/",
            HTTP_AUTHORIZATION="Bearer token123",
            HTTP_X_API_KEY="secret123",
        )
        request.user = self.user

        data = capture_request_data(request)

        self.assertNotIn("authorization", data["headers"])
        self.assertNotIn("x_api_key", data["headers"])


class TestFormatTraceback(DrfCommonTestCase):
    """Test format_traceback function."""

    def test_format_traceback_no_args(self):
        """format_traceback returns formatted exception traceback."""
        try:
            raise ValueError("test error")
        except ValueError:
            tb_str = format_traceback()
            self.assertIn("ValueError: test error", tb_str)
            self.assertIn("Traceback", tb_str)

    def test_format_traceback_with_tb(self):
        """format_traceback formats provided traceback."""
        try:
            raise ValueError("test error")
        except ValueError as e:
            tb_str = format_traceback(e.__traceback__)
            self.assertIn("raise ValueError", tb_str)


class TestLogModelChanges(DrfCommonTestCase):
    """Test log_model_changes function."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_log_model_changes_with_user(self):
        """log_model_changes logs changes with user."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["models"]
        ):
            with capture_logs("models.changes") as log_output:
                log_model_changes(self.user, "create", self.user)

                expected = f"CREATE: User {self.user.pk} by {self.user}"
                self.assertIn(expected, log_output.getvalue())

    def test_log_model_changes_without_user(self):
        """log_model_changes logs changes without user."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["models"]
        ):
            with capture_logs("models.changes") as log_output:
                log_model_changes(self.user, "delete")

                expected = f"DELETE: User {self.user.pk} by system"
                self.assertIn(expected, log_output.getvalue())

    @patch("drf_commons.debug.utils.Categories.get_logger")
    def test_log_model_changes_logs_field_deltas_for_updates(self, mock_get_logger):
        logger = Mock()
        mock_get_logger.return_value = logger
        
        class TrackedUser:
            def __init__(self):
                self.pk = 1
                self._state = object()
                self._original_values = {
                    "email": "old@example.com",
                    "username": "same",
                }
                self.email = "new@example.com"
                self.username = "same"

        instance = TrackedUser()
        instance._meta = SimpleNamespace(
            fields=[
                SimpleNamespace(name="email"),
                SimpleNamespace(name="username"),
            ]
        )

        log_model_changes(instance, action="update", user="auditor")

        logger.info.assert_called_once_with("UPDATE: TrackedUser 1 by auditor")
        logger.debug.assert_called_once()
        self.assertIn('"email": {"old": "old@example.com", "new": "new@example.com"}', logger.debug.call_args.args[0])

    @patch("drf_commons.debug.utils.Categories.get_logger")
    def test_log_model_changes_warns_when_change_capture_fails(self, mock_get_logger):
        logger = Mock()
        mock_get_logger.return_value = logger

        class BrokenInstance:
            pk = 5
            _state = object()
            _original_values = {"name": "old"}
            _meta = SimpleNamespace(fields=[SimpleNamespace(name="name")])

            @property
            def name(self):
                raise RuntimeError("broken attribute")

        log_model_changes(BrokenInstance(), action="update", user="auditor")

        logger.warning.assert_called_once()
        self.assertIn("Could not log field changes", logger.warning.call_args.args[0])


class TestDebugCacheOperations(DrfCommonTestCase):
    """Test debug_cache_operations function."""

    def test_debug_cache_get_hit(self):
        """debug_cache_operations logs cache hit."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["cache"]
        ):
            with capture_logs("cache.operations") as log_output:
                debug_cache_operations("user:123", "get", "cached_value", 0.001)

                expected = "Cache GET: user:123 - HIT - Duration: 0.0010s"
                self.assertIn(expected, log_output.getvalue())

    def test_debug_cache_get_miss(self):
        """debug_cache_operations logs cache miss."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["cache"]
        ):
            with capture_logs("cache.operations") as log_output:
                debug_cache_operations("user:456", "get")

                expected = "Cache GET: user:456 - MISS"
                self.assertIn(expected, log_output.getvalue())

    def test_debug_cache_non_get_reports_boolean_success(self):
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["cache"]
        ):
            with capture_logs("cache.operations") as log_output:
                debug_cache_operations("user:789", "set", result=False)

                self.assertIn(
                    "Cache SET: user:789 - Success: False",
                    log_output.getvalue(),
                )


class TestProfileFunction(DrfCommonTestCase):
    """Test profile_function function."""

    def test_profile_function_enabled(self):
        """profile_function profiles when performance category is enabled."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["performance"]
        ):

            def test_func():
                return "result"

            result, profile_output = profile_function(test_func)

            self.assertEqual(result, "result")
            self.assertIsInstance(profile_output, str)

    def test_profile_function_disabled(self):
        """profile_function returns result without profiling when disabled."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=[]
        ):

            def test_func():
                return "result"

            result, profile_output = profile_function(test_func)

            self.assertEqual(result, "result")
            self.assertIsNone(profile_output)

    def test_profile_function_returns_fallback_message_when_profiling_fails(self):
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["performance"]
        ):
            state = {"calls": 0}

            def flaky_func():
                state["calls"] += 1
                if state["calls"] == 1:
                    raise RuntimeError("boom")
                return "recovered"

            result, profile_output = profile_function(flaky_func)

            self.assertEqual(result, "recovered")
            self.assertEqual(profile_output, "Profiling failed: boom")


class TestMemoryUsage(DrfCommonTestCase):
    """Test memory_usage function."""

    @patch("drf_commons.debug.utils.importlib.import_module")
    def test_memory_usage_with_psutil(self, mock_import_module):
        """memory_usage returns memory info when psutil is available."""
        mock_psutil = Mock()
        mock_process = Mock()
        mock_memory_info = Mock()
        mock_memory_info.rss = 1024000
        mock_memory_info.vms = 2048000
        mock_process.memory_info.return_value = mock_memory_info
        mock_process.memory_percent.return_value = 5.5

        mock_virtual_memory = Mock()
        mock_virtual_memory.available = 8192000000

        mock_psutil.Process.return_value = mock_process
        mock_psutil.virtual_memory.return_value = mock_virtual_memory
        mock_import_module.return_value = mock_psutil

        result = memory_usage()

        expected = {
            "rss": 1024000,
            "vms": 2048000,
            "percent": 5.5,
            "available": 8192000000,
        }
        self.assertEqual(result, expected)

    @patch("drf_commons.debug.utils.importlib.import_module")
    def test_memory_usage_raises_helpful_error_when_psutil_missing(
        self, mock_import_module
    ):
        """memory_usage should raise install guidance when psutil is unavailable."""
        mock_import_module.side_effect = ImportError("No module named psutil")

        with self.assertRaises(ImportError) as cm:
            memory_usage()

        self.assertIn("drf-commons[debug]", str(cm.exception))


class TestAnalyzeQueryset(DrfCommonTestCase):
    """Test analyze_queryset function."""

    def test_analyze_queryset_enabled(self):
        """analyze_queryset analyzes when database category is enabled."""
        User = get_user_model()

        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["database"]
        ):
            with capture_logs("queryset.analysis") as log_output:
                queryset = User.objects.all()
                analyze_queryset(queryset, "Test Users")

                self.assertIn("Analyzing Test Users:", log_output.getvalue())

    @patch("drf_commons.debug.utils.Categories.get_logger", return_value=Categories._null_logger)
    def test_analyze_queryset_skips_sampling_for_null_logger(self, mock_get_logger):
        queryset = MagicMock()
        queryset.query = "SELECT 1"
        queryset.count.return_value = 0

        analyze_queryset(queryset, "Silent QuerySet")

        queryset.__getitem__.assert_not_called()

    @patch("drf_commons.debug.utils.Categories.get_logger")
    def test_analyze_queryset_warns_when_sampling_fails(self, mock_get_logger):
        logger = Mock()
        mock_get_logger.return_value = logger

        class BrokenQuerySet:
            query = "SELECT 1"

            def count(self):
                return 1

            def __getitem__(self, item):
                raise RuntimeError("cannot slice")

        analyze_queryset(BrokenQuerySet(), "Broken QuerySet")

        logger.warning.assert_called_once_with("Could not fetch sample items: cannot slice")


class TestDebugContextProcessor(DrfCommonTestCase):
    """Test debug_context_processor function."""

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.user = UserFactory()

    def test_debug_context_processor_enabled(self):
        """debug_context_processor returns context when requests category is enabled."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["requests"]
        ):
            request = self.factory.get("/test/")
            request.user = self.user

            context = debug_context_processor(request)

            self.assertIn("debug_info", context)
            self.assertEqual(context["debug_info"]["user"], str(self.user))
            self.assertEqual(context["debug_info"]["path"], "/test/")
            self.assertEqual(context["debug_info"]["method"], "GET")

    def test_debug_context_processor_disabled(self):
        """debug_context_processor returns empty dict when requests category is disabled."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=[]
        ):
            request = self.factory.get("/test/")
            context = debug_context_processor(request)

            self.assertEqual(context, {})

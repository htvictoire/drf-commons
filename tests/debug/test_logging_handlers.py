"""
Tests for debug logging handler building functions.
"""

from pathlib import Path
from unittest.mock import patch

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.debug.logging.handlers import (
    build_handlers,
    filter_available_handlers,
    _should_skip_handler,
    _build_console_handler,
    _build_file_handler,
)
from drf_commons.debug.core.categories import Categories


class BuildConsoleHandlerTests(DrfCommonTestCase):
    """Tests for _build_console_handler."""

    def test_returns_stream_handler_config(self):
        """_build_console_handler returns StreamHandler class config."""
        spec = {"class": "logging.StreamHandler", "level": "INFO"}
        result = _build_console_handler(spec, debug_mode=False)
        self.assertEqual(result["class"], "logging.StreamHandler")

    def test_level_is_debug_when_debug_mode_true(self):
        """_build_console_handler sets level to DEBUG when debug_mode is True."""
        spec = {"class": "logging.StreamHandler", "level": "INFO"}
        result = _build_console_handler(spec, debug_mode=True)
        self.assertEqual(result["level"], "DEBUG")

    def test_level_from_spec_when_debug_mode_false(self):
        """_build_console_handler uses spec level when debug_mode is False."""
        spec = {"class": "logging.StreamHandler", "level": "WARNING"}
        result = _build_console_handler(spec, debug_mode=False)
        self.assertEqual(result["level"], "WARNING")

    def test_formatter_is_verbose(self):
        """_build_console_handler always uses verbose formatter."""
        spec = {"class": "logging.StreamHandler", "level": "INFO"}
        result = _build_console_handler(spec, debug_mode=False)
        self.assertEqual(result["formatter"], "verbose")


class BuildFileHandlerTests(DrfCommonTestCase):
    """Tests for _build_file_handler."""

    def setUp(self):
        super().setUp()
        self.logs_dir = Path("/tmp/test_logs")
        self.spec = {
            "file": "main.log",
            "level": "INFO",
            "max_bytes": 10 * 1024 * 1024,
            "backup_count": 5,
        }

    def test_returns_rotating_file_handler_config(self):
        """_build_file_handler returns RotatingFileHandler class config."""
        result = _build_file_handler(self.logs_dir, self.spec)
        self.assertEqual(result["class"], "logging.handlers.RotatingFileHandler")

    def test_filename_combines_logs_dir_and_spec_file(self):
        """_build_file_handler constructs filename from logs_dir and spec file."""
        result = _build_file_handler(self.logs_dir, self.spec)
        self.assertIn("main.log", result["filename"])
        self.assertIn("/tmp/test_logs", result["filename"])

    def test_returns_correct_max_bytes(self):
        """_build_file_handler includes maxBytes from spec."""
        result = _build_file_handler(self.logs_dir, self.spec)
        self.assertEqual(result["maxBytes"], self.spec["max_bytes"])

    def test_returns_correct_backup_count(self):
        """_build_file_handler includes backupCount from spec."""
        result = _build_file_handler(self.logs_dir, self.spec)
        self.assertEqual(result["backupCount"], self.spec["backup_count"])

    def test_returns_correct_level(self):
        """_build_file_handler includes level from spec."""
        result = _build_file_handler(self.logs_dir, self.spec)
        self.assertEqual(result["level"], "INFO")

    def test_formatter_is_verbose(self):
        """_build_file_handler uses verbose formatter."""
        result = _build_file_handler(self.logs_dir, self.spec)
        self.assertEqual(result["formatter"], "verbose")

    def test_raises_value_error_for_invalid_path(self):
        """_build_file_handler raises ValueError when logs_dir is invalid type."""
        bad_spec = {
            "file": "main.log",
            "level": "INFO",
            "max_bytes": 1024,
            "backup_count": 1,
        }
        with self.assertRaises((ValueError, TypeError)):
            _build_file_handler(None, bad_spec)


class ShouldSkipHandlerTests(DrfCommonTestCase):
    """Tests for _should_skip_handler."""

    def test_skips_category_handler_when_category_not_enabled(self):
        """_should_skip_handler returns True for category handler when category disabled."""
        result = _should_skip_handler(
            Categories.USERS,
            {"file": "users.log", "level": "INFO"},
            enabled_categories=set(),
        )
        self.assertTrue(result)

    def test_does_not_skip_category_handler_when_category_enabled(self):
        """_should_skip_handler returns False for category handler when category enabled."""
        result = _should_skip_handler(
            Categories.USERS,
            {"file": "users.log", "level": "INFO"},
            enabled_categories={Categories.USERS},
        )
        self.assertFalse(result)

    def test_skips_when_required_category_not_enabled(self):
        """_should_skip_handler returns True when required_category is not in enabled_categories."""
        spec = {
            "file": "slow_queries.log",
            "level": "WARNING",
            "requires_category": Categories.DATABASE,
        }
        result = _should_skip_handler("database_slow", spec, enabled_categories=set())
        self.assertTrue(result)

    def test_does_not_skip_when_required_category_is_enabled(self):
        """_should_skip_handler returns False when required_category is enabled."""
        spec = {
            "file": "slow_queries.log",
            "level": "WARNING",
            "requires_category": Categories.DATABASE,
        }
        result = _should_skip_handler(
            "database_slow", spec, enabled_categories={Categories.DATABASE}
        )
        self.assertFalse(result)

    def test_does_not_skip_non_category_handler(self):
        """_should_skip_handler returns False for handlers that are not category handlers."""
        spec = {"class": "logging.StreamHandler", "level": "INFO"}
        result = _should_skip_handler("console", spec, enabled_categories=set())
        self.assertFalse(result)


class BuildHandlersTests(DrfCommonTestCase):
    """Tests for build_handlers."""

    def setUp(self):
        super().setUp()
        self.logs_dir = Path("/tmp/test_logs")

    def test_includes_console_handler(self):
        """build_handlers includes console handler (it is not category-specific)."""
        handlers = build_handlers(self.logs_dir, enabled_categories=set(), debug_mode=False)
        self.assertIn("console", handlers)

    def test_excludes_disabled_category_handlers(self):
        """build_handlers excludes handlers for disabled categories."""
        handlers = build_handlers(self.logs_dir, enabled_categories=set(), debug_mode=False)
        self.assertNotIn(Categories.USERS, handlers)
        self.assertNotIn(Categories.API, handlers)

    def test_includes_enabled_category_handlers(self):
        """build_handlers includes handlers for enabled categories."""
        handlers = build_handlers(
            self.logs_dir,
            enabled_categories={Categories.USERS},
            debug_mode=False,
        )
        self.assertIn(Categories.USERS, handlers)

    def test_console_handler_debug_level_in_debug_mode(self):
        """build_handlers sets console handler to DEBUG level in debug mode."""
        handlers = build_handlers(self.logs_dir, enabled_categories=set(), debug_mode=True)
        self.assertEqual(handlers["console"]["level"], "DEBUG")

    def test_handler_creation_exception_is_caught_and_skipped(self):
        """build_handlers skips a handler when creation raises TypeError/ValueError/KeyError."""
        # Inject a spec that will cause a ValueError in _build_file_handler
        bad_spec = {
            "file": None,  # None will cause path construction to fail
            "level": "INFO",
            "max_bytes": 1024,
            "backup_count": 1,
        }
        from drf_commons.debug.logging.handlers import HANDLER_SPECS

        with patch.dict(HANDLER_SPECS, {"bad_handler": bad_spec}, clear=False):
            # Should not raise
            handlers = build_handlers(self.logs_dir, enabled_categories=set(), debug_mode=False)
        # bad_handler should not be in result
        self.assertNotIn("bad_handler", handlers)


class FilterAvailableHandlersTests(DrfCommonTestCase):
    """Tests for filter_available_handlers."""

    def test_filters_out_unavailable_handlers(self):
        """filter_available_handlers removes names not in available_handlers."""
        result = filter_available_handlers(
            ["console", "users", "missing"],
            available_handlers={"console", "users"},
        )
        self.assertIn("console", result)
        self.assertIn("users", result)
        self.assertNotIn("missing", result)

    def test_returns_empty_list_when_none_available(self):
        """filter_available_handlers returns empty list when no names match."""
        result = filter_available_handlers(["a", "b"], available_handlers=set())
        self.assertEqual(result, [])

    def test_returns_all_when_all_available(self):
        """filter_available_handlers returns all names when all are available."""
        names = ["console", "main", "errors"]
        result = filter_available_handlers(names, available_handlers=set(names))
        self.assertEqual(sorted(result), sorted(names))

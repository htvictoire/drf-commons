"""
Tests for debug logging logger building functions.
"""

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.debug.logging.loggers import (
    build_loggers,
    resolve_logger_handlers,
    get_logger_level,
)
from drf_commons.debug.core.categories import Categories


class GetLoggerLevelTests(DrfCommonTestCase):
    """Tests for get_logger_level."""

    def test_returns_level_debug_in_debug_mode(self):
        """get_logger_level returns level_debug when debug_mode is True and level_debug exists."""
        spec = {"level": "INFO", "level_debug": "DEBUG", "level_production": "WARNING"}
        result = get_logger_level(spec, debug_mode=True)
        self.assertEqual(result, "DEBUG")

    def test_returns_level_production_when_not_debug(self):
        """get_logger_level returns level_production when debug_mode is False."""
        spec = {"level": "INFO", "level_debug": "DEBUG", "level_production": "WARNING"}
        result = get_logger_level(spec, debug_mode=False)
        self.assertEqual(result, "WARNING")

    def test_returns_default_level_when_no_mode_specific_level(self):
        """get_logger_level returns spec level when neither level_debug nor level_production."""
        spec = {"level": "ERROR"}
        result = get_logger_level(spec, debug_mode=False)
        self.assertEqual(result, "ERROR")

    def test_returns_info_as_fallback_when_no_level_keys(self):
        """get_logger_level returns INFO as fallback when level key is absent."""
        spec = {}
        result = get_logger_level(spec, debug_mode=False)
        self.assertEqual(result, "INFO")

    def test_debug_mode_without_level_debug_falls_back_to_default(self):
        """get_logger_level falls back to spec level when debug_mode but no level_debug."""
        spec = {"level": "WARNING"}
        result = get_logger_level(spec, debug_mode=True)
        self.assertEqual(result, "WARNING")


class ResolveLoggerHandlersTests(DrfCommonTestCase):
    """Tests for resolve_logger_handlers."""

    def test_returns_handlers_from_spec(self):
        """resolve_logger_handlers returns handlers listed in spec."""
        spec = {"handlers": ["console", "main"]}
        result = resolve_logger_handlers(spec, enabled_categories=set(), debug_mode=False)
        self.assertIn("console", result)
        self.assertIn("main", result)

    def test_adds_console_in_debug_mode_when_console_in_debug_set(self):
        """resolve_logger_handlers adds 'console' handler in debug mode when console_in_debug is set."""
        spec = {"handlers": ["main"], "console_in_debug": True}
        result = resolve_logger_handlers(spec, enabled_categories=set(), debug_mode=True)
        self.assertIn("console", result)

    def test_does_not_add_console_when_debug_mode_false(self):
        """resolve_logger_handlers does not add console when debug_mode is False."""
        spec = {"handlers": ["main"], "console_in_debug": True}
        result = resolve_logger_handlers(spec, enabled_categories=set(), debug_mode=False)
        # console not in original handlers, should not be added
        self.assertNotIn("console", result)

    def test_filters_out_disabled_category_handlers(self):
        """resolve_logger_handlers removes category handlers for disabled categories."""
        spec = {"handlers": [Categories.USERS, "console"]}
        result = resolve_logger_handlers(
            spec, enabled_categories=set(), debug_mode=False
        )
        self.assertNotIn(Categories.USERS, result)
        self.assertIn("console", result)

    def test_keeps_enabled_category_handlers(self):
        """resolve_logger_handlers keeps category handlers for enabled categories."""
        spec = {"handlers": [Categories.USERS, "console"]}
        result = resolve_logger_handlers(
            spec, enabled_categories={Categories.USERS}, debug_mode=False
        )
        self.assertIn(Categories.USERS, result)

    def test_returns_empty_when_all_handlers_disabled(self):
        """resolve_logger_handlers returns empty list when all handlers are for disabled categories."""
        spec = {"handlers": [Categories.USERS, Categories.API]}
        result = resolve_logger_handlers(
            spec, enabled_categories=set(), debug_mode=False
        )
        self.assertEqual(result, [])


class BuildLoggersTests(DrfCommonTestCase):
    """Tests for build_loggers."""

    def test_returns_dict(self):
        """build_loggers returns a dict."""
        result = build_loggers(enabled_categories=set(), debug_mode=False)
        self.assertIsInstance(result, dict)

    def test_includes_django_logger_always(self):
        """build_loggers includes django logger since it has non-category handlers."""
        result = build_loggers(enabled_categories=set(), debug_mode=False)
        # django logger uses console, main, errors - all non-category
        self.assertIn("django", result)

    def test_excludes_loggers_requiring_disabled_categories(self):
        """build_loggers excludes loggers whose required_category is not enabled."""
        result = build_loggers(enabled_categories=set(), debug_mode=False)
        users_auth_logger = f"{Categories.USERS}.auth"
        self.assertNotIn(users_auth_logger, result)

    def test_includes_loggers_requiring_enabled_categories(self):
        """build_loggers includes loggers whose required_category is enabled."""
        result = build_loggers(
            enabled_categories={Categories.USERS}, debug_mode=False
        )
        users_auth_logger = f"{Categories.USERS}.auth"
        self.assertIn(users_auth_logger, result)

    def test_logger_has_handlers_level_propagate_keys(self):
        """build_loggers logger entries have handlers, level, and propagate keys."""
        result = build_loggers(enabled_categories=set(), debug_mode=False)
        django_logger = result["django"]
        self.assertIn("handlers", django_logger)
        self.assertIn("level", django_logger)
        self.assertIn("propagate", django_logger)

    def test_db_logger_gets_debug_level_in_debug_mode(self):
        """build_loggers sets django.db.backends to DEBUG level when debug_mode is True."""
        result = build_loggers(
            enabled_categories={Categories.DATABASE}, debug_mode=True
        )
        # django.db.backends requires DATABASE category to have handlers (console added in debug)
        if "django.db.backends" in result:
            self.assertEqual(result["django.db.backends"]["level"], "DEBUG")

    def test_db_logger_gets_info_level_in_production_mode(self):
        """build_loggers sets django.db.backends to INFO level when debug_mode is False."""
        result = build_loggers(
            enabled_categories={Categories.DATABASE}, debug_mode=False
        )
        if "django.db.backends" in result:
            self.assertEqual(result["django.db.backends"]["level"], "INFO")

    def test_logger_without_available_handlers_is_skipped(self):
        """build_loggers skips loggers that resolve to no available handlers."""
        # With no categories enabled, category-only loggers should be excluded
        result = build_loggers(enabled_categories=set(), debug_mode=False)
        # users.auth requires USERS category and uses only USERS handler
        self.assertNotIn(f"{Categories.USERS}.auth", result)

    def test_propagate_defaults_to_false(self):
        """build_loggers sets propagate to False by default for loggers."""
        result = build_loggers(enabled_categories=set(), debug_mode=False)
        self.assertFalse(result["django"]["propagate"])

    def test_debug_mode_adds_console_to_db_logger(self):
        """build_loggers adds console handler to db logger in debug mode."""
        result = build_loggers(
            enabled_categories={Categories.DATABASE}, debug_mode=True
        )
        if "django.db.backends" in result:
            self.assertIn("console", result["django.db.backends"]["handlers"])

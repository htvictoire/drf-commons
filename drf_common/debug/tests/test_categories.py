"""
Tests for debug Categories and NullLogger classes.
"""

import logging

from drf_common.common_tests.base_cases import DrfCommonTestCase
from drf_common.common_tests.utils import override_debug_settings

from drf_common.debug.core.categories import Categories, NullLogger


class TestNullLogger(DrfCommonTestCase):
    """Test NullLogger absorbs all logging calls."""

    def setUp(self):
        super().setUp()
        self.null_logger = NullLogger()

    def test_null_logger_debug(self):
        """NullLogger debug method does nothing."""
        self.null_logger.debug("test message")

    def test_null_logger_info(self):
        """NullLogger info method does nothing."""
        self.null_logger.info("test message")

    def test_null_logger_warning(self):
        """NullLogger warning method does nothing."""
        self.null_logger.warning("test message")

    def test_null_logger_error(self):
        """NullLogger error method does nothing."""
        self.null_logger.error("test message")

    def test_null_logger_critical(self):
        """NullLogger critical method does nothing."""
        self.null_logger.critical("test message")

    def test_null_logger_exception(self):
        """NullLogger exception method does nothing."""
        self.null_logger.exception("test message")

    def test_null_logger_log(self):
        """NullLogger log method does nothing."""
        self.null_logger.log(logging.INFO, "test message")

    def test_null_logger_handlers(self):
        """NullLogger handler methods do nothing."""
        handler = logging.StreamHandler()
        self.null_logger.addHandler(handler)
        self.null_logger.removeHandler(handler)

    def test_null_logger_set_level(self):
        """NullLogger setLevel does nothing."""
        self.null_logger.setLevel(logging.DEBUG)


class TestCategories(DrfCommonTestCase):
    """Test Categories class functionality."""

    def test_category_constants(self):
        """Categories class defines expected constants."""
        expected_categories = [
            "users",
            "api",
            "database",
            "models",
            "cache",
            "performance",
            "errors",
            "requests",
        ]

        for category in expected_categories:
            self.assertTrue(hasattr(Categories, category.upper()))
            self.assertEqual(getattr(Categories, category.upper()), category)

        self.assertEqual(set(Categories.ALL), set(expected_categories))

    def test_is_enabled_not_in_enabled_list(self):
        """Category not in DEBUG_ENABLED_LOG_CATEGORIES is disabled."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors"]
        ):
            self.assertFalse(Categories.is_enabled("users"))
            self.assertTrue(Categories.is_enabled("errors"))

    def test_is_enabled_production_safe_only(self):
        """In production, only safe categories are enabled."""
        with override_debug_settings(
            DEBUG=False,
            COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors", "users", "performance"],
            COMMON_DEBUG_PRODUCTION_SAFE_CATEGORIES=["errors", "performance"],
        ):
            self.assertTrue(Categories.is_enabled("errors"))
            self.assertTrue(Categories.is_enabled("performance"))
            self.assertFalse(Categories.is_enabled("users"))

    def test_is_enabled_development_all_enabled(self):
        """In development, all enabled categories are allowed."""
        with override_debug_settings(
            DEBUG=True,
            COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors", "users", "api"],
            COMMON_DEBUG_PRODUCTION_SAFE_CATEGORIES=["errors"],
        ):
            self.assertTrue(Categories.is_enabled("errors"))
            self.assertTrue(Categories.is_enabled("users"))
            self.assertTrue(Categories.is_enabled("api"))

    def test_get_enabled_returns_set(self):
        """get_enabled returns set of enabled categories."""
        with override_debug_settings(
            COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors", "users"]
        ):
            enabled = Categories.get_enabled()
            self.assertEqual(enabled, {"errors", "users"})

    def test_get_logger_enabled_category(self):
        """get_logger returns real logger for enabled category."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors"]
        ):
            logger = Categories.get_logger("test.logger", "errors")
            self.assertIsInstance(logger, logging.Logger)
            self.assertEqual(logger.name, "test.logger")

    def test_get_logger_disabled_category(self):
        """get_logger returns NullLogger for disabled category."""
        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors"]
        ):
            logger = Categories.get_logger("test.logger", "users")
            self.assertIsInstance(logger, NullLogger)

    def test_get_logger_no_category(self):
        """get_logger with no category always returns real logger."""
        logger = Categories.get_logger("test.logger")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test.logger")

    def test_null_logger_singleton(self):
        """NullLogger uses singleton instance."""
        logger1 = Categories.get_logger("test1", "disabled_category")
        logger2 = Categories.get_logger("test2", "disabled_category")

        with override_debug_settings(
            DEBUG=True, COMMON_DEBUG_ENABLED_LOG_CATEGORIES=[]
        ):
            self.assertIs(logger1, logger2)
            self.assertIs(logger1, Categories._null_logger)

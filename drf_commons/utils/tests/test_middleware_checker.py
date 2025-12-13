"""
Tests for middleware dependency checker.
"""

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from ..middleware_checker import MiddlewareChecker, require_middleware


class MiddlewareCheckerTestCase(DrfCommonTestCase):
    """Test middleware checker functionality."""

    def test_middleware_checker_installed(self):
        """Test MiddlewareChecker when middleware is installed."""
        with override_settings(
            MIDDLEWARE=[
                "drf_commons.middlewares.current_user.CurrentUserMiddleware",
            ]
        ):
            # Should not raise an exception
            checker = MiddlewareChecker(
                "drf_commons.middlewares.current_user.CurrentUserMiddleware",
                "TestFeature",
            )
            self.assertTrue(checker.is_installed())

    def test_middleware_checker_not_installed(self):
        """Test MiddlewareChecker when middleware is not installed."""
        with override_settings(
            MIDDLEWARE=[
                "django.middleware.security.SecurityMiddleware",
            ]
        ):
            with self.assertRaises(ImproperlyConfigured) as cm:
                MiddlewareChecker(
                    "drf_commons.middlewares.current_user.CurrentUserMiddleware",
                    "TestFeature",
                )

            error_message = str(cm.exception)
            self.assertIn("TestFeature requires", error_message)
            self.assertIn("CurrentUserMiddleware", error_message)

    def test_require_middleware_decorator_success(self):
        """Test require_middleware decorator when middleware is installed."""
        with override_settings(
            MIDDLEWARE=[
                "drf_commons.middlewares.current_user.CurrentUserMiddleware",
            ]
        ):
            # Should not raise an exception during decoration
            @require_middleware(
                "drf_commons.middlewares.current_user.CurrentUserMiddleware",
                "TestFeature",
            )
            def test_function():
                return True

            self.assertTrue(test_function())

    def test_require_middleware_decorator_failure(self):
        """Test require_middleware decorator when middleware is not installed."""
        with override_settings(
            MIDDLEWARE=[
                "django.middleware.security.SecurityMiddleware",
            ]
        ):
            with self.assertRaises(ImproperlyConfigured) as cm:

                @require_middleware(
                    "drf_commons.middlewares.current_user.CurrentUserMiddleware",
                    "TestFeature",
                )
                def test_function():
                    return True

            error_message = str(cm.exception)
            self.assertIn("TestFeature requires", error_message)
            self.assertIn("CurrentUserMiddleware", error_message)

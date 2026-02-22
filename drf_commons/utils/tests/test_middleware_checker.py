"""
Tests for middleware dependency checker.
"""

from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from ..middleware_checker import (
    MiddlewareChecker,
    enforce_current_user_middleware_if_used,
    require_middleware,
)


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
            @require_middleware(
                "drf_commons.middlewares.current_user.CurrentUserMiddleware",
                "TestFeature",
            )
            def test_function():
                return True

            with self.assertRaises(ImproperlyConfigured) as cm:
                test_function()

            error_message = str(cm.exception)
            self.assertIn("TestFeature requires", error_message)
            self.assertIn("CurrentUserMiddleware", error_message)

    @patch("drf_commons.utils.middleware_checker.enforce_middleware")
    @patch("drf_commons.utils.middleware_checker._model_uses_current_user_features")
    @patch("drf_commons.utils.middleware_checker.apps.get_models")
    def test_enforce_current_user_middleware_if_used_runs_when_feature_present(
        self, mock_get_models, mock_uses_features, mock_enforce
    ):
        """Startup check should enforce middleware only when features are used."""
        mock_get_models.return_value = [object(), object()]
        mock_uses_features.side_effect = [False, True]

        used = enforce_current_user_middleware_if_used()

        self.assertTrue(used)
        mock_enforce.assert_called_once_with(
            "drf_commons.middlewares.current_user.CurrentUserMiddleware",
            "UserActionMixin/CurrentUserField",
        )

    @patch("drf_commons.utils.middleware_checker.enforce_middleware")
    @patch("drf_commons.utils.middleware_checker._model_uses_current_user_features")
    @patch("drf_commons.utils.middleware_checker.apps.get_models")
    def test_enforce_current_user_middleware_if_used_skips_when_feature_absent(
        self, mock_get_models, mock_uses_features, mock_enforce
    ):
        """Startup check should skip middleware enforcement when feature is unused."""
        mock_get_models.return_value = [object(), object()]
        mock_uses_features.side_effect = [False, False]

        used = enforce_current_user_middleware_if_used()

        self.assertFalse(used)
        mock_enforce.assert_not_called()

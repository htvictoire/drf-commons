"""
Middleware dependency checker for drf-common library.

This module provides utilities to check if required middlewares are installed
before using features that depend on them.
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class MiddlewareChecker:
    """Generic middleware dependency checker."""

    def __init__(self, middleware_path, feature_name):
        """
        Initialize middleware checker and automatically check requirements.

        Args:
            middleware_path (str): Full path to required middleware class
            feature_name (str): Name of feature that requires the middleware

        Raises:
            ImproperlyConfigured: If middleware is not installed
        """
        self.middleware_path = middleware_path
        self.feature_name = feature_name
        self.require()

    def is_installed(self):
        """
        Check if the middleware is installed in Django settings.

        Returns:
            bool: True if middleware is installed, False otherwise
        """
        middleware_list = getattr(settings, "MIDDLEWARE", [])
        return self.middleware_path in middleware_list

    def require(self):
        """
        Ensure middleware is installed, raise error if not.

        Raises:
            ImproperlyConfigured: If middleware is not installed
        """
        if not self.is_installed():
            raise ImproperlyConfigured(
                f"{self.feature_name} requires '{self.middleware_path}' "
                f"to be added to MIDDLEWARE setting."
            )


def require_middleware(middleware_path, feature_name):
    """
    Decorator to check middleware dependencies before class/function execution.

    Args:
        middleware_path (str): Full path to required middleware
        feature_name (str): Name of feature for error message

    Returns:
        function: Decorator function
    """

    def decorator(cls_or_func):
        MiddlewareChecker(middleware_path, feature_name)
        return cls_or_func

    return decorator

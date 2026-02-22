"""
Middleware dependency checker for drf-commons library.

This module provides utilities to check if required middlewares are installed
before using features that depend on them.
"""

from functools import wraps

from django.apps import apps
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
        @wraps(cls_or_func)
        def wrapped(*args, **kwargs):
            MiddlewareChecker(middleware_path, feature_name)
            return cls_or_func(*args, **kwargs)

        return wrapped

    return decorator


def enforce_middleware(middleware_path, feature_name):
    """Runtime middleware requirement check for feature execution paths."""
    MiddlewareChecker(middleware_path, feature_name)


def _model_uses_current_user_features(model):
    """Return True if model uses UserActionMixin or CurrentUserField."""
    from drf_commons.models.fields import CurrentUserField
    from drf_commons.models.mixins import UserActionMixin

    if issubclass(model, UserActionMixin):
        return True

    for field in model._meta.get_fields():
        if isinstance(field, CurrentUserField):
            return True

    return False


def enforce_current_user_middleware_if_used():
    """
    Enforce current-user middleware only when loaded models use related features.
    """
    middleware_path = "drf_commons.middlewares.current_user.CurrentUserMiddleware"
    uses_current_user_features = any(
        _model_uses_current_user_features(model) for model in apps.get_models()
    )
    if uses_current_user_features:
        enforce_middleware(middleware_path, "UserActionMixin/CurrentUserField")
    return uses_current_user_features

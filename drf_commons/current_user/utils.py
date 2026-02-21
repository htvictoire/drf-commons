"""
Current user utilities backed by ContextVar storage.
"""

from contextvars import ContextVar

from drf_commons.common_conf import settings

USER_ATTR_NAME = settings.LOCAL_USER_ATTR_NAME

_current_user_var = ContextVar(USER_ATTR_NAME, default=None)


def _set_current_user(user=None):
    """
    Set current user in the active context and return reset token.
    """
    return _current_user_var.set(user)


def _reset_current_user(token):
    """
    Reset current user context to the previous value represented by token.
    """
    _current_user_var.reset(token)


def _clear_current_user():
    """
    Clear current user for the active context.
    """
    _current_user_var.set(None)


def get_current_user():
    """Get the current user from context-local storage."""
    return _current_user_var.get()


def get_current_authenticated_user():
    """Get current authenticated user, returns None for anonymous users."""
    current_user = get_current_user()
    if current_user is None:
        return None
    if not getattr(current_user, "is_authenticated", False):
        return None
    return current_user

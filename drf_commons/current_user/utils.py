"""
Current user utilities for thread-local user access.
"""

from threading import local

from django.contrib.auth.models import AnonymousUser

from drf_commons.common_conf import settings

USER_ATTR_NAME = settings.LOCAL_USER_ATTR_NAME

_thread_locals = local()


def _do_set_current_user(user_fun):
    setattr(_thread_locals, USER_ATTR_NAME, user_fun.__get__(user_fun, local))


def _set_current_user(user=None):
    """
    Sets current user in local thread.

    Can be used as a hook e.g. for shell jobs (when request object is not
    available).
    """
    _do_set_current_user(lambda self: user)


def get_current_user():
    """Get the current user from thread-local storage."""
    current_user = getattr(_thread_locals, USER_ATTR_NAME, None)
    if callable(current_user):
        return current_user()
    return current_user


def get_current_authenticated_user():
    """Get current authenticated user, returns None for anonymous users."""
    current_user = get_current_user()
    if isinstance(current_user, AnonymousUser):
        return None
    return current_user

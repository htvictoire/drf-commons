"""
Current user middleware for thread-local user access.
"""

from ..current_user.utils import _do_set_current_user


class SetCurrentUser:
    def __init__(this, request):
        this.request = request

    def __enter__(this):
        _do_set_current_user(lambda self: getattr(this.request, 'user', None))

    def __exit__(this, type, value, traceback):
        _do_set_current_user(lambda self: None)


class CurrentUserMiddleware(object):
    """Middleware to set current user in thread-local storage."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # request.user closure; asserts laziness;
        # memorization is implemented in
        # request.user (non-data descriptor)
        with SetCurrentUser(request):
            response = self.get_response(request)
        return response

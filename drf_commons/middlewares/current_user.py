"""
Current user middleware for context-local user access.
"""

from asgiref.sync import iscoroutinefunction, markcoroutinefunction

from drf_commons.current_user.utils import _reset_current_user, _set_current_user


class CurrentUserMiddleware(object):
    """Middleware to set current user in context-local storage."""

    sync_capable = True
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        self.is_async = iscoroutinefunction(get_response)
        if self.is_async:
            markcoroutinefunction(self)

    def __call__(self, request):
        if self.is_async:
            return self.__acall__(request)

        token = _set_current_user(getattr(request, "user", None))
        try:
            response = self.get_response(request)
        finally:
            _reset_current_user(token)
        return response

    async def __acall__(self, request):
        token = _set_current_user(getattr(request, "user", None))
        try:
            response = await self.get_response(request)
        finally:
            _reset_current_user(token)
        return response

"""
Tests for current user middleware.
"""

import asyncio
from unittest.mock import Mock, patch

from django.test import RequestFactory

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.common_tests.factories import UserFactory

from ..current_user import CurrentUserMiddleware


class CurrentUserMiddlewareTests(DrfCommonTestCase):
    """Tests for CurrentUserMiddleware."""

    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()

    def test_middleware_initialization(self):
        """Middleware stores get_response and sync/async capability flags."""
        get_response = Mock()
        middleware = CurrentUserMiddleware(get_response)

        self.assertEqual(middleware.get_response, get_response)
        self.assertFalse(middleware.is_async)
        self.assertTrue(middleware.sync_capable)
        self.assertTrue(middleware.async_capable)

    @patch("drf_commons.middlewares.current_user._reset_current_user")
    @patch("drf_commons.middlewares.current_user._set_current_user")
    def test_middleware_sync_call_sets_and_resets_context(
        self, mock_set_current_user, mock_reset_current_user
    ):
        """Sync middleware call should always reset user context."""
        token = object()
        mock_set_current_user.return_value = token
        get_response = Mock(return_value=Mock())
        middleware = CurrentUserMiddleware(get_response)

        user = UserFactory()
        request = self.factory.get("/")
        request.user = user

        response = middleware(request)

        mock_set_current_user.assert_called_once_with(user)
        mock_reset_current_user.assert_called_once_with(token)
        get_response.assert_called_once_with(request)
        self.assertEqual(response, get_response.return_value)

    @patch("drf_commons.middlewares.current_user._reset_current_user")
    @patch("drf_commons.middlewares.current_user._set_current_user")
    def test_middleware_sync_call_resets_context_on_exception(
        self, mock_set_current_user, mock_reset_current_user
    ):
        """Sync middleware must reset context even if view raises."""
        token = object()
        mock_set_current_user.return_value = token
        get_response = Mock(side_effect=ValueError("boom"))
        middleware = CurrentUserMiddleware(get_response)

        request = self.factory.get("/")
        request.user = UserFactory()

        with self.assertRaises(ValueError):
            middleware(request)

        mock_set_current_user.assert_called_once()
        mock_reset_current_user.assert_called_once_with(token)

    @patch("drf_commons.middlewares.current_user._reset_current_user")
    @patch("drf_commons.middlewares.current_user._set_current_user")
    def test_middleware_async_call_sets_and_resets_context(
        self, mock_set_current_user, mock_reset_current_user
    ):
        """Async middleware path should set and reset context around await."""
        token = object()
        mock_set_current_user.return_value = token

        async def get_response(request):
            return {"ok": True, "path": request.path}

        middleware = CurrentUserMiddleware(get_response)
        request = self.factory.get("/async/")
        request.user = UserFactory()

        result = asyncio.run(middleware(request))

        self.assertTrue(middleware.is_async)
        self.assertEqual(result["ok"], True)
        self.assertEqual(result["path"], "/async/")
        mock_set_current_user.assert_called_once_with(request.user)
        mock_reset_current_user.assert_called_once_with(token)

    @patch("drf_commons.middlewares.current_user._reset_current_user")
    @patch("drf_commons.middlewares.current_user._set_current_user")
    def test_middleware_async_call_resets_context_on_exception(
        self, mock_set_current_user, mock_reset_current_user
    ):
        """Async middleware must reset context even if awaited view raises."""
        token = object()
        mock_set_current_user.return_value = token

        async def get_response(_request):
            raise ValueError("async boom")

        middleware = CurrentUserMiddleware(get_response)
        request = self.factory.get("/async/")
        request.user = UserFactory()

        with self.assertRaises(ValueError):
            asyncio.run(middleware(request))

        mock_set_current_user.assert_called_once()
        mock_reset_current_user.assert_called_once_with(token)

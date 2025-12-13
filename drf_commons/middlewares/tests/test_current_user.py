"""
Tests for current user middleware.
"""

from unittest.mock import Mock, patch

from django.test import RequestFactory

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.common_tests.factories import UserFactory

from ..current_user import CurrentUserMiddleware, SetCurrentUser


class SetCurrentUserTests(DrfCommonTestCase):
    """Tests for SetCurrentUser context manager."""

    def setUp(self):
        """Set up test dependencies."""
        super().setUp()
        self.factory = RequestFactory()

    @patch("middlewares.current_user._do_set_current_user")
    def test_context_manager_with_user(self, mock_set_current_user):
        """Test SetCurrentUser context manager with authenticated user."""
        user = UserFactory()
        request = self.factory.get("/")
        request.user = user

        with SetCurrentUser(request):
            # Verify user was set on enter
            mock_set_current_user.assert_called()
            # Get the lambda function that was passed
            set_user_func = mock_set_current_user.call_args[0][0]
            # Test that it returns the correct user
            self.assertEqual(set_user_func(None), user)

        # Verify user was cleared on exit (second call)
        self.assertEqual(mock_set_current_user.call_count, 2)
        clear_user_func = mock_set_current_user.call_args_list[1][0][0]
        self.assertIsNone(clear_user_func(None))

    @patch("middlewares.current_user._do_set_current_user")
    def test_context_manager_without_user(self, mock_set_current_user):
        """Test SetCurrentUser context manager with no user on request."""
        request = self.factory.get("/")
        # No user attribute on request

        with SetCurrentUser(request):
            # Verify function was called on enter
            mock_set_current_user.assert_called()
            set_user_func = mock_set_current_user.call_args[0][0]
            # Should return None when no user attribute
            self.assertIsNone(set_user_func(None))

        # Verify clear function was called on exit
        self.assertEqual(mock_set_current_user.call_count, 2)

    @patch("middlewares.current_user._do_set_current_user")
    def test_context_manager_with_exception(self, mock_set_current_user):
        """Test SetCurrentUser context manager handles exceptions properly."""
        user = UserFactory()
        request = self.factory.get("/")
        request.user = user

        with self.assertRaises(ValueError):
            with SetCurrentUser(request):
                raise ValueError("Test exception")

        # Should still call clear on exception
        self.assertEqual(mock_set_current_user.call_count, 2)
        clear_user_func = mock_set_current_user.call_args_list[1][0][0]
        self.assertIsNone(clear_user_func(None))

    @patch("middlewares.current_user._do_set_current_user")
    def test_context_manager_user_attribute_none(self, mock_set_current_user):
        """Test SetCurrentUser when request.user is None."""
        request = self.factory.get("/")
        request.user = None

        with SetCurrentUser(request):
            set_user_func = mock_set_current_user.call_args[0][0]
            self.assertIsNone(set_user_func(None))


class CurrentUserMiddlewareTests(DrfCommonTestCase):
    """Tests for CurrentUserMiddleware."""

    def setUp(self):
        """Set up test dependencies."""
        super().setUp()
        self.factory = RequestFactory()

    def test_middleware_initialization(self):
        """Test middleware initialization."""
        get_response = Mock()
        middleware = CurrentUserMiddleware(get_response)

        self.assertEqual(middleware.get_response, get_response)

    @patch("middlewares.current_user.SetCurrentUser")
    def test_middleware_call_success(self, mock_set_current_user):
        """Test successful middleware execution."""
        get_response = Mock()
        get_response.return_value = Mock()
        middleware = CurrentUserMiddleware(get_response)

        request = self.factory.get("/")
        response = middleware(request)

        # Verify SetCurrentUser context manager was used
        mock_set_current_user.assert_called_once_with(request)
        mock_set_current_user.return_value.__enter__.assert_called_once()
        mock_set_current_user.return_value.__exit__.assert_called_once()

        # Verify get_response was called
        get_response.assert_called_once_with(request)
        self.assertEqual(response, get_response.return_value)

    @patch("middlewares.current_user.SetCurrentUser")
    def test_middleware_call_with_exception(self, mock_set_current_user):
        """Test middleware execution when get_response raises exception."""
        get_response = Mock()
        get_response.side_effect = ValueError("Response error")
        middleware = CurrentUserMiddleware(get_response)

        request = self.factory.get("/")

        with self.assertRaises(ValueError):
            middleware(request)

        # Verify context manager was still properly used
        mock_set_current_user.assert_called_once_with(request)
        mock_set_current_user.return_value.__enter__.assert_called_once()
        mock_set_current_user.return_value.__exit__.assert_called_once()

    @patch("middlewares.current_user.SetCurrentUser")
    def test_middleware_with_different_request_types(self, mock_set_current_user):
        """Test middleware with different request types."""
        get_response = Mock(return_value=Mock())
        middleware = CurrentUserMiddleware(get_response)

        # Test GET request
        get_request = self.factory.get("/test/")
        middleware(get_request)

        # Test POST request
        post_request = self.factory.post("/test/", data={"key": "value"})
        middleware(post_request)

        # Test PUT request
        put_request = self.factory.put("/test/")
        middleware(put_request)

        # Verify SetCurrentUser was called for each request
        self.assertEqual(mock_set_current_user.call_count, 3)
        mock_set_current_user.assert_any_call(get_request)
        mock_set_current_user.assert_any_call(post_request)
        mock_set_current_user.assert_any_call(put_request)

    @patch("middlewares.current_user.SetCurrentUser")
    def test_middleware_preserves_response(self, mock_set_current_user):
        """Test that middleware preserves the exact response from get_response."""
        # Create a custom response object
        custom_response = Mock()
        custom_response.status_code = 201
        custom_response.content = b"Custom content"

        get_response = Mock(return_value=custom_response)
        middleware = CurrentUserMiddleware(get_response)

        request = self.factory.post("/test/")
        response = middleware(request)

        # Response should be exactly what get_response returned
        self.assertEqual(response, custom_response)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.content, b"Custom content")

    def test_middleware_integration_with_real_context_manager(self):
        """Test middleware integration with actual SetCurrentUser context manager."""
        get_response = Mock()
        response_mock = Mock()
        get_response.return_value = response_mock

        middleware = CurrentUserMiddleware(get_response)

        user = UserFactory()
        request = self.factory.get("/test/")
        request.user = user

        with patch("middlewares.current_user._do_set_current_user") as mock_set_user:
            response = middleware(request)

            # Verify the context manager was used correctly
            self.assertEqual(mock_set_user.call_count, 2)  # Enter and exit
            self.assertEqual(response, response_mock)
            get_response.assert_called_once_with(request)

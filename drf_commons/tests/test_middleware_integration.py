"""
Middleware integration tests with real request/response cycles.

Tests middleware behavior in actual Django request processing.
"""

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings
from django.urls import path

from drf_commons.common_tests.factories import UserFactory
from drf_commons.current_user.utils import get_current_user
from drf_commons.middlewares.current_user import CurrentUserMiddleware
from drf_commons.middlewares.debug import DebugMiddleware

User = get_user_model()


def middleware_test_view(request):
    """Simple test view that returns current user info."""
    from django.contrib.auth.models import AnonymousUser
    current_user = get_current_user()
    if current_user is None:
        username = 'None'
    elif isinstance(current_user, AnonymousUser):
        username = 'None'
    else:
        username = current_user.username
    return HttpResponse(f"Current user: {username}")


def slow_view(request):
    """Test view that simulates slow processing."""
    import time
    time.sleep(0.1)  # 100ms delay
    return HttpResponse("Slow response")


def query_heavy_view(request):
    """Test view that makes multiple database queries."""
    # Make multiple queries to test SQL debugging
    User.objects.count()
    User.objects.filter(is_active=True).count()
    User.objects.filter(is_staff=False).count()
    return HttpResponse("Query heavy response")


# Test URLs
test_urlpatterns = [
    path('test/', middleware_test_view, name='test_view'),
    path('slow/', slow_view, name='slow_view'),
    path('queries/', query_heavy_view, name='query_view'),
]


class CurrentUserMiddlewareIntegrationTests(TestCase):
    """Test CurrentUserMiddleware in real request/response cycle."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory(username="middleware_test_user")
        self.middleware = CurrentUserMiddleware(middleware_test_view)

    def test_middleware_sets_current_user_in_thread_local(self):
        """Test middleware makes user available via get_current_user()."""
        request = self.factory.get('/test/')
        request.user = self.user

        response = self.middleware(request)

        # Verify the view received the correct user
        self.assertEqual(response.content.decode(), "Current user: middleware_test_user")

    def test_middleware_handles_anonymous_user(self):
        """Test middleware works with anonymous users."""
        from django.contrib.auth.models import AnonymousUser

        request = self.factory.get('/test/')
        request.user = AnonymousUser()

        response = self.middleware(request)

        # get_current_user() should return None for AnonymousUser
        self.assertEqual(response.content.decode(), "Current user: None")

    def test_middleware_cleans_up_current_user_context(self):
        """Test middleware cleans up current-user context after request."""
        request = self.factory.get('/test/')
        request.user = self.user

        # Before request
        initial_user = get_current_user()
        self.assertIsNone(initial_user)

        # During request
        response = self.middleware(request)
        self.assertIn("middleware_test_user", response.content.decode())

        # After request - should be cleaned up
        final_user = get_current_user()
        self.assertIsNone(final_user)

    def test_middleware_with_multiple_requests(self):
        """Test middleware handles multiple sequential requests correctly."""
        user1 = UserFactory(username="user1")
        user2 = UserFactory(username="user2")

        # First request
        request1 = self.factory.get('/test/')
        request1.user = user1
        response1 = self.middleware(request1)
        self.assertEqual(response1.content.decode(), "Current user: user1")

        # Second request with different user
        request2 = self.factory.get('/test/')
        request2.user = user2
        response2 = self.middleware(request2)
        self.assertEqual(response2.content.decode(), "Current user: user2")

        # Verify no cross-contamination
        self.assertNotEqual(response1.content, response2.content)


@override_settings(
    DEBUG=True,
    DEBUG_ENABLED_LOG_CATEGORIES=["requests", "queries", "performance"],
    MIDDLEWARE=[
        'drf_commons.middlewares.debug.DebugMiddleware',
    ]
)
class DebugMiddlewareIntegrationTests(TestCase):
    """Test DebugMiddleware in real request/response cycle."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory()

    def test_debug_middleware_logs_request_response_cycle(self):
        """Test debug middleware captures request/response timing."""
        with self.assertLogs('middleware.debug', level='INFO') as log_output:
            response = self.client.get('/test/')
            self.assertEqual(response.status_code, 200)

        # Verify request logging occurred
        log_messages = ' '.join(log_output.output)
        self.assertIn("Request started: GET /test/", log_messages)

    def test_debug_middleware_tracks_query_count(self):
        """Test debug middleware tracks database query count."""
        with self.assertLogs('middleware.debug', level='INFO') as log_output:
            response = self.client.get('/queries/')
            self.assertEqual(response.status_code, 200)

        # Verify query tracking in logs
        log_messages = ' '.join(log_output.output)
        self.assertIn("queries", log_messages.lower())

    def test_debug_middleware_measures_response_time(self):
        """Test debug middleware measures response time for slow requests."""
        with self.assertLogs('middleware.debug', level='INFO') as log_output:
            response = self.client.get('/slow/')
            self.assertEqual(response.status_code, 200)

        # Verify timing information in logs
        log_messages = ' '.join(log_output.output)
        self.assertIn("duration", log_messages.lower())

    def test_debug_middleware_handles_authenticated_requests(self):
        """Test debug middleware logs user information for authenticated requests."""
        with self.assertLogs('middleware.debug', level='DEBUG') as log_output:
            self.client.force_login(self.user)
            response = self.client.get('/test/')
            self.assertEqual(response.status_code, 200)

        # Verify user information appears in logs
        log_messages = ' '.join(log_output.output)
        self.assertIn("User:", log_messages)

    def test_debug_middleware_handles_request_parameters(self):
        """Test debug middleware logs query parameters."""
        with self.assertLogs('middleware.debug', level='DEBUG') as log_output:
            response = self.client.get('/test/?param1=value1&param2=value2')
            self.assertEqual(response.status_code, 200)

        # Verify query parameters in logs
        log_messages = ' '.join(log_output.output)
        self.assertIn("param1", log_messages)
        self.assertIn("value1", log_messages)


@override_settings(
    DEBUG=True,
    DEBUG_ENABLED_LOG_CATEGORIES=["requests", "queries", "performance"],
    MIDDLEWARE=[
        'drf_commons.middlewares.debug.DebugMiddleware',
    ]
)
class MiddlewareStackIntegrationTests(TestCase):
    """Test multiple middlewares working together."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = UserFactory(username="stack_test_user")

    def test_middleware_stack_order(self):
        """Test middlewares work correctly when stacked together."""
        with self.assertLogs('middleware.debug', level='INFO') as log_output:
            response = self.client.get('/test/')
            self.assertEqual(response.status_code, 200)

        # Verify debug logging occurred
        log_messages = ' '.join(log_output.output)
        self.assertIn("Request started:", log_messages)
        self.assertIn("Request completed:", log_messages)

    def test_middleware_error_handling(self):
        """Test middleware stack handles errors gracefully."""
        def error_view(request):
            raise ValueError("Test error")

        debug_middleware = DebugMiddleware(
            CurrentUserMiddleware(error_view)
        )

        request = self.factory.get('/test/')
        request.user = self.user

        # Middleware should not suppress the exception
        with self.assertRaises(ValueError):
            debug_middleware(request)

        # But current user should still be cleaned up
        final_user = get_current_user()
        self.assertIsNone(final_user)

    def test_middleware_with_no_user_attribute(self):
        """Test middleware handles requests without user attribute."""
        def no_user_view(request):
            current_user = get_current_user()
            return HttpResponse(f"User: {current_user}")

        middleware = CurrentUserMiddleware(no_user_view)

        request = self.factory.get('/test/')
        # Don't set request.user

        response = middleware(request)
        self.assertEqual(response.content.decode(), "User: None")

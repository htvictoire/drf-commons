"""
Tests for current user thread-local utilities.
"""

from django.contrib.auth.models import AnonymousUser

from drf_commons.common_conf import settings
from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.common_tests.factories import UserFactory

from drf_commons.current_user.utils import (
    USER_ATTR_NAME,
    _set_current_user,
    _thread_locals,
    get_current_authenticated_user,
    get_current_user,
)


class TestCurrentUserUtils(DrfCommonTestCase):
    """Test thread-local user utilities."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_set_current_user(self):
        """_set_current_user stores user in thread-local storage."""
        _set_current_user(self.user)

        stored_user = get_current_user()
        self.assertEqual(stored_user, self.user)

    def test_set_current_user_none(self):
        """_set_current_user can store None."""
        _set_current_user(None)

        stored_user = get_current_user()
        self.assertIsNone(stored_user)

    def test_get_current_user_not_set(self):
        """get_current_user returns None when no user is set."""
        # Ensure thread-local is clean
        if hasattr(_thread_locals, USER_ATTR_NAME):
            delattr(_thread_locals, USER_ATTR_NAME)

        stored_user = get_current_user()
        self.assertIsNone(stored_user)

    def test_get_current_user_callable(self):
        """get_current_user handles callable stored user."""
        _set_current_user(self.user)

        # The internal implementation uses a callable
        stored_user = get_current_user()
        self.assertEqual(stored_user, self.user)

    def test_get_current_authenticated_user_authenticated(self):
        """get_current_authenticated_user returns authenticated user."""
        _set_current_user(self.user)

        authenticated_user = get_current_authenticated_user()
        self.assertEqual(authenticated_user, self.user)

    def test_get_current_authenticated_user_anonymous(self):
        """get_current_authenticated_user returns None for anonymous user."""
        anonymous_user = AnonymousUser()
        _set_current_user(anonymous_user)

        authenticated_user = get_current_authenticated_user()
        self.assertIsNone(authenticated_user)

    def test_get_current_authenticated_user_none(self):
        """get_current_authenticated_user returns None when no user set."""
        _set_current_user(None)

        authenticated_user = get_current_authenticated_user()
        self.assertIsNone(authenticated_user)

    def test_thread_isolation(self):
        """Thread-local storage isolates users between tests."""
        # This test verifies that setUp/tearDown properly cleans thread-locals
        _set_current_user(self.user)

        stored_user = get_current_user()
        self.assertEqual(stored_user, self.user)

        # After cleanup, should be None in new test context
        self._cleanup_thread_locals()
        stored_user = get_current_user()
        self.assertIsNone(stored_user)

    def test_user_attr_name_setting(self):
        """USER_ATTR_NAME uses the configured setting."""
        expected_name = settings.LOCAL_USER_ATTR_NAME
        self.assertEqual(USER_ATTR_NAME, expected_name)

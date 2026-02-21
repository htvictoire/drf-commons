"""
Tests for current user context-local utilities.
"""

from django.contrib.auth.models import AnonymousUser

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.common_tests.factories import UserFactory

from drf_commons.current_user.utils import (
    _clear_current_user,
    _current_user_var,
    _reset_current_user,
    _set_current_user,
    get_current_authenticated_user,
    get_current_user,
)


class TestCurrentUserUtils(DrfCommonTestCase):
    """Test context-local user utilities."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()

    def test_set_current_user(self):
        """_set_current_user stores user in current context."""
        _set_current_user(self.user)

        stored_user = get_current_user()
        self.assertEqual(stored_user, self.user)

    def test_set_current_user_none(self):
        """_set_current_user can store None."""
        _set_current_user(None)

        stored_user = get_current_user()
        self.assertIsNone(stored_user)

    def test_get_current_user_not_set(self):
        """get_current_user returns None when user context is cleared."""
        _clear_current_user()

        stored_user = get_current_user()
        self.assertIsNone(stored_user)

    def test_get_current_user_direct_value(self):
        """get_current_user returns the direct value in the current context."""
        _set_current_user(self.user)
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

    def test_context_clear(self):
        """Clearing context removes current user."""
        _set_current_user(self.user)
        _clear_current_user()
        self.assertIsNone(get_current_user())

    def test_reset_current_user_restores_previous_value(self):
        """ContextVar token reset restores previous user value."""
        _clear_current_user()
        initial_token = _set_current_user(self.user)
        other_user = UserFactory()
        token = _set_current_user(other_user)

        self.assertEqual(get_current_user(), other_user)
        _reset_current_user(token)
        self.assertEqual(get_current_user(), self.user)

        _reset_current_user(initial_token)
        self.assertIsNone(_current_user_var.get())

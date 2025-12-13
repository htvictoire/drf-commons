"""
pytest configuration and shared fixtures for DRF Common library tests.
"""

from django.contrib.auth import get_user_model
from django.test import override_settings

import pytest
from rest_framework.test import APIClient

from .factories import UserFactory

User = get_user_model()


@pytest.fixture
def user():
    """Create a test user."""
    return UserFactory()


@pytest.fixture
def authenticated_user():
    """Create an authenticated test user."""
    return UserFactory(is_active=True)


@pytest.fixture
def api_client():
    """DRF API client for testing API endpoints."""
    return APIClient()


@pytest.fixture
def authenticated_api_client(authenticated_user):
    """API client with authenticated user."""
    client = APIClient()
    client.force_authenticate(user=authenticated_user)
    return client


@pytest.fixture
def test_settings():
    """Override Django settings for testing."""
    with override_settings(
        CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}},
        CELERY_TASK_ALWAYS_EAGER=True,
        COMMON_DEBUG_ENABLED_LOG_CATEGORIES=["errors"],
    ):
        yield


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests."""
    pass

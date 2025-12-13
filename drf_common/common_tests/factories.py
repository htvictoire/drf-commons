"""
Factory Boy factories for DRF Common library tests.
"""

from django.contrib.auth import get_user_model

import factory
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return

        password = extracted or "testpass123"
        self.set_password(password)
        self.save()


class StaffUserFactory(UserFactory):
    """Factory for creating staff users."""

    is_staff = True


class SuperUserFactory(UserFactory):
    """Factory for creating superusers."""

    is_staff = True
    is_superuser = True


class APIRequestFactoryWithUser:
    """Request factory that creates requests with authenticated user."""

    def __init__(self, user=None):
        self.factory = APIRequestFactory()
        self.user = user or UserFactory()

    def get(self, path, data=None, **extra):
        """Create GET request with authenticated user."""
        request = self.factory.get(path, data, **extra)
        request.user = self.user
        return Request(request)

    def post(self, path, data=None, **extra):
        """Create POST request with authenticated user."""
        request = self.factory.post(path, data, **extra)
        request.user = self.user
        return Request(request)

    def patch(self, path, data=None, **extra):
        """Create PATCH request with authenticated user."""
        request = self.factory.patch(path, data, **extra)
        request.user = self.user
        return Request(request)

    def delete(self, path, data=None, **extra):
        """Create DELETE request with authenticated user."""
        request = self.factory.delete(path, data, **extra)
        request.user = self.user
        return Request(request)

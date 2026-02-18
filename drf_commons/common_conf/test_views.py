"""
Minimal views used by test URL configuration.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse

from drf_commons.current_user.utils import get_current_user

User = get_user_model()


def middleware_test_view(request):
    """Simple view that returns current user info."""
    current_user = get_current_user()
    if current_user is None:
        username = "None"
    elif isinstance(current_user, AnonymousUser):
        username = "None"
    else:
        username = current_user.username
    return HttpResponse(f"Current user: {username}")


def slow_view(request):
    """View that simulates slow processing."""
    import time

    time.sleep(0.1)
    return HttpResponse("Slow response")


def query_heavy_view(request):
    """View that performs multiple queries."""
    User.objects.count()
    User.objects.filter(is_active=True).count()
    User.objects.filter(is_staff=False).count()
    return HttpResponse("Query heavy response")

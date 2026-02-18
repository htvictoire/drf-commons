"""
URL configuration for testing.
"""

from django.urls import path

from drf_commons.common_conf.test_views import (
    middleware_test_view,
    query_heavy_view,
    slow_view,
)

urlpatterns = [
    path('test/', middleware_test_view, name='test_view'),
    path('slow/', slow_view, name='slow_view'),
    path('queries/', query_heavy_view, name='query_view'),
]

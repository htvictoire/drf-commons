"""
Tests for drf_commons.urls module.
"""

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.urls import urlpatterns


class UrlsTests(DrfCommonTestCase):
    """Tests for drf_commons URL configuration."""

    def test_urlpatterns_is_list(self):
        """urlpatterns must be a list."""
        self.assertIsInstance(urlpatterns, list)

    def test_urlpatterns_is_empty(self):
        """drf_commons exposes no URL routes by default."""
        self.assertEqual(urlpatterns, [])

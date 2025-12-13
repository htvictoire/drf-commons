"""
Tests for pagination classes.
"""

from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from ..base import LimitOffsetPaginationWithFormat, StandardPageNumberPagination


class StandardPageNumberPaginationTestCase(DrfCommonTestCase):
    """Test StandardPageNumberPagination class."""

    def setUp(self):
        super().setUp()
        self.pagination = StandardPageNumberPagination()

    def test_pagination_settings(self):
        """Test pagination has correct default settings."""
        self.assertEqual(self.pagination.page_size, 20)
        self.assertEqual(self.pagination.page_size_query_param, "page_size")
        self.assertEqual(self.pagination.max_page_size, 100)

    def test_pagination_inherits_from_page_number_pagination(self):
        """Test pagination inherits from DRF PageNumberPagination."""
        self.assertIsInstance(self.pagination, PageNumberPagination)


class LimitOffsetPaginationWithFormatTestCase(DrfCommonTestCase):
    """Test LimitOffsetPaginationWithFormat class."""

    def setUp(self):
        super().setUp()
        self.pagination = LimitOffsetPaginationWithFormat()

    def test_pagination_settings(self):
        """Test pagination has correct default settings."""
        self.assertEqual(self.pagination.default_limit, 20)
        self.assertEqual(self.pagination.limit_query_param, "limit")
        self.assertEqual(self.pagination.offset_query_param, "offset")
        self.assertEqual(self.pagination.max_limit, 100)

    def test_pagination_inherits_from_limit_offset_pagination(self):
        """Test pagination inherits from DRF LimitOffsetPagination."""
        self.assertIsInstance(self.pagination, LimitOffsetPagination)

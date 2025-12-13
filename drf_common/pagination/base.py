"""
Standard pagination classes for the application.
"""

from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination


class StandardPageNumberPagination(PageNumberPagination):
    """
    Standard pagination class with reasonable defaults.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class LimitOffsetPaginationWithFormat(LimitOffsetPagination):
    """
    Limit/offset pagination with reasonable defaults.
    """

    default_limit = 20
    limit_query_param = "limit"
    offset_query_param = "offset"
    max_limit = 100

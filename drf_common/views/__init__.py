"""
Common views package for enhanced Django REST Framework functionality.

Provides modular mixins and composed viewsets for various use cases.
"""

from .base import (
    BaseViewSet,
    BulkCreateViewSet,
    BulkDeleteViewSet,
    BulkImportableViewSet,
    BulkOnlyViewSet,
    BulkUpdateViewSet,
    BulkViewSet,
    CreateListViewSet,
    ImportableViewSet,
    ReadOnlyViewSet,
)
from .mixins import (
    BulkCreateModelMixin,
    BulkDeleteModelMixin,
    BulkUpdateModelMixin,
    CreateModelMixin,
    DestroyModelMixin,
    FileExportMixin,
    FileImportMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)

__all__ = [
    # Mixins
    "CreateModelMixin",
    "ListModelMixin",
    "RetrieveModelMixin",
    "UpdateModelMixin",
    "DestroyModelMixin",
    "BulkCreateModelMixin",
    "BulkUpdateModelMixin",
    "BulkDeleteModelMixin",
    "FileImportMixin",
    "FileExportMixin",
    # ViewSets
    "BaseViewSet",
    "BulkViewSet",
    "ReadOnlyViewSet",
    "CreateListViewSet",
    "BulkCreateViewSet",
    "BulkUpdateViewSet",
    "BulkDeleteViewSet",
    "BulkOnlyViewSet",
    "ImportableViewSet",
    "BulkImportableViewSet",
]

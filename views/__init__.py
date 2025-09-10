"""
Common views package for enhanced Django REST Framework functionality.

Provides modular mixins and composed viewsets for various use cases.
"""

from .mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    BulkCreateModelMixin,
    BulkUpdateModelMixin,
    BulkDeleteModelMixin,
    FileImportMixin,
    FileExportMixin,
)

from .base import (
    BaseViewSet,
    BulkViewSet,
    ReadOnlyViewSet,
    CreateListViewSet,
    BulkCreateViewSet,
    BulkUpdateViewSet,
    BulkDeleteViewSet,
    BulkOnlyViewSet,
    ImportableViewSet,
    BulkImportableViewSet,
)

__all__ = [
    # Mixins
    'CreateModelMixin',
    'ListModelMixin',
    'RetrieveModelMixin',
    'UpdateModelMixin',
    'DestroyModelMixin',
    'BulkCreateModelMixin',
    'BulkUpdateModelMixin',
    'BulkDeleteModelMixin',
    'FileImportMixin',
    'FileExportMixin',

    # ViewSets
    'BaseViewSet',
    'BulkViewSet',
    'ReadOnlyViewSet',
    'CreateListViewSet',
    'BulkCreateViewSet',
    'BulkUpdateViewSet',
    'BulkDeleteViewSet',
    'BulkOnlyViewSet',
    'ImportableViewSet',
    'BulkImportableViewSet',
]
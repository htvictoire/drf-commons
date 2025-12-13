"""
DRF Common View Mixins

This package provides mixins for Django REST Framework ViewSets to handle
common operations like CRUD, bulk operations, and file import/export.

Usage:
    from drf_common.views.mixins import CreateModelMixin, ListModelMixin
    from drf_common.views.mixins.bulk import BulkCreateModelMixin
    from drf_common.views.mixins.import_export import FileImportMixin
"""

# Import bulk operation mixins
from .bulk import (
    BulkCreateModelMixin,
    BulkDeleteModelMixin,
    BulkOperationMixin,
    BulkUpdateModelMixin,
)

# Import all CRUD mixins for backward compatibility
from .crud import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)

# Import file import/export mixins
from .import_export import (
    FileExportMixin,
    FileImportMixin,
)

__all__ = [
    # CRUD mixins
    "CreateModelMixin",
    "ListModelMixin",
    "RetrieveModelMixin",
    "UpdateModelMixin",
    "DestroyModelMixin",
    # Bulk operation mixins
    "BulkOperationMixin",
    "BulkCreateModelMixin",
    "BulkUpdateModelMixin",
    "BulkDeleteModelMixin",
    # Import/Export mixins
    "FileImportMixin",
    "FileExportMixin",
]

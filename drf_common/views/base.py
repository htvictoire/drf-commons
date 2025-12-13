"""
ViewSets combining mixins for various use cases.
"""

from rest_framework import viewsets

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


class BaseViewSet(
    viewsets.GenericViewSet,
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    DestroyModelMixin,
    FileExportMixin,
):
    """
    Complete ViewSet with all CRUD operations.
    User tracking is handled automatically by the base model.
    """

    return_data_on_create = True
    return_data_on_update = True


class BulkViewSet(
    BaseViewSet,
    BulkCreateModelMixin,
    BulkUpdateModelMixin,
    BulkDeleteModelMixin,
):
    """
    ViewSet with all CRUD operations plus bulk operations.
    """

    pass


class ReadOnlyViewSet(
    viewsets.GenericViewSet,
    ListModelMixin,
    RetrieveModelMixin,
    FileExportMixin,
):
    """
    ViewSet that only allows reading data (list and retrieve).
    """

    pass


class CreateListViewSet(
    viewsets.GenericViewSet,
    CreateModelMixin,
    ListModelMixin,
    FileExportMixin,
):
    """
    ViewSet that allows creating and listing objects only.
    """

    return_data_on_create = True


class BulkCreateViewSet(
    viewsets.GenericViewSet,
    BulkCreateModelMixin,
):
    """
    ViewSet that only allows bulk create operations.
    """

    pass


class BulkUpdateViewSet(
    viewsets.GenericViewSet,
    BulkUpdateModelMixin,
):
    """
    ViewSet that only allows bulk update operations.
    """

    pass


class BulkDeleteViewSet(
    viewsets.GenericViewSet,
    BulkDeleteModelMixin,
):
    """
    ViewSet that only allows bulk delete operations.
    """

    pass


class BulkOnlyViewSet(
    viewsets.GenericViewSet,
    BulkCreateModelMixin,
    BulkUpdateModelMixin,
    BulkDeleteModelMixin,
):
    """
    ViewSet that only provides bulk operations (no individual CRUD).
    """

    pass


class ImportableViewSet(
    BaseViewSet,
    FileImportMixin,
):
    """
    Complete ViewSet with all CRUD operations plus file import capability.

    To use, define import_file_config in your viewset:

    class MyViewSet(ImportableViewSet):
        import_file_config = {
            "file_format": "xlsx",  # or "csv", "xls"
            "order": ["main"],
            "models": {
                "main": {
                    "model": "myapp.MyModel",
                    "direct_columns": {
                        "name": "Name",
                        "email": "Email"
                    }
                }
            }
        }

        # Optional transforms
        import_transforms = {
            "hash_password": my_hash_function
        }
    """

    pass


class BulkImportableViewSet(
    BulkViewSet,
    FileImportMixin,
):
    """
    ViewSet with all CRUD operations, bulk operations, plus file import capability.
    """

    pass

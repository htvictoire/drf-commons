"""
Mixins for bulk operations: create, update, delete.
"""

from typing import Any, Dict, List

from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from drf_common.common_conf.settings import BULK_OPERATION_BATCH_SIZE
from drf_common.response.utils import error_response, success_response
from .crud import CreateModelMixin, DestroyModelMixin, UpdateModelMixin
from .utils import get_model_name


class BulkOperationMixin:
    """
    Mixin for bulk operations: create, update, delete.
    """

    bulk_batch_size = BULK_OPERATION_BATCH_SIZE  # Max items per bulk operation

    def validate_bulk_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate bulk operation data."""
        if not data:
            raise ValidationError(
                f"Data cannot be empty for {self.__class__.__name__} objects bulk operation."
            )

        if not isinstance(data, list):
            raise ValidationError(
                f"Data must be a list of objects for {self.__class__.__name__}."
            )

        if len(data) > self.bulk_batch_size:
            raise ValidationError(
                f"Batch size cannot exceed {self.bulk_batch_size} items for {self.__class__.__name__}."
            )

        return data


class BulkCreateModelMixin(CreateModelMixin, BulkOperationMixin):
    """
    Bulk create model instances.
    """

    bulk_batch_size = BULK_OPERATION_BATCH_SIZE

    def on_create_message(self):
        return super().on_create_message() + " (bulk operation)"

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create(self, request: Request, *args, **kwargs) -> Response:
        """Create multiple objects in a single request."""
        try:
            self.validate_bulk_data(request.data)
            with transaction.atomic():
                kwargs["many_on_create"] = True
                return self.create(request, *args, **kwargs)
        except ValidationError as e:
            return error_response(
                errors=e.detail,
                message="Bulk create validation failed: " + str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class BulkUpdateModelMixin(UpdateModelMixin, BulkOperationMixin):
    """
    Bulk update model instances.
    """

    bulk_batch_size = BULK_OPERATION_BATCH_SIZE

    def on_update_message(self):
        return super().on_update_message() + " (bulk operation)"

    @action(detail=False, methods=["put"], url_path="bulk-update")
    def bulk_update(self, request: Request, *args, **kwargs) -> Response:
        """Update multiple objects in a single request."""
        try:
            self.validate_bulk_data(request.data)
            kwargs["many_on_update"] = True
            with transaction.atomic():
                return self.update(request, partial=True, *args, **kwargs)
        except ValidationError as e:
            return error_response(
                errors=e.detail,
                message="Bulk update validation failed: " + str(e),
                status_code=status.HTTP_400_BAD_REQUEST,
            )


class BulkDeleteModelMixin(DestroyModelMixin, BulkOperationMixin):
    """
    Bulk delete model instances.
    """

    bulk_batch_size = BULK_OPERATION_BATCH_SIZE

    def _validate_delete_ids(self, ids, operation_name="delete"):
        """Common validation for bulk delete operations."""
        if not isinstance(ids, list):
            raise ValidationError("IDs must be provided as a list.")

        if not ids:
            raise ValidationError("IDs list cannot be empty.")

        if len(ids) > self.bulk_batch_size:
            raise ValidationError(
                f"Cannot {operation_name} more than {self.bulk_batch_size} items at once."
            )

    def _get_queryset_data(self, ids):
        """Get queryset and process found/missing objects."""
        queryset = self.get_queryset().filter(pk__in=ids)
        found_objects = list(queryset)
        found_ids = [str(obj.pk) for obj in found_objects]
        missing_ids = set(map(str, ids)) - set(found_ids)

        return queryset, found_objects, missing_ids

    def _build_base_response_data(self, ids, missing_ids, count=0):
        """Build base response data structure."""
        missing_list = list(missing_ids) if missing_ids else []
        response_data = {
            "requested_count": len(ids),
            "missing_ids": missing_list,
            "missing_count": len(missing_list),
            "count": count,
        }
        return response_data

    def _get_bulk_message(self, action_type, count=None):
        """Generate bulk operation message."""
        if count is not None:
            return f"Bulk {action_type} completed. {count} {get_model_name(self)} {action_type}d."
        return f"Bulk {action_type} operation completed."

    def on_bulk_delete_message(self, deleted_count=None):
        """Message for successful bulk delete operation."""
        return self._get_bulk_message("delete", deleted_count)

    def on_bulk_soft_delete_message(self, deleted_count=None):
        """Message for successful bulk soft delete operation."""
        return self._get_bulk_message("soft delete", deleted_count)

    @action(detail=False, methods=["delete"])
    def bulk_delete(self, request: Request) -> Response:
        """Delete multiple objects in a single request."""
        ids = request.data

        try:
            self._validate_delete_ids(ids, "delete")

            with transaction.atomic():
                queryset, found_objects, missing_ids = self._get_queryset_data(ids)

                deleted_count = 0
                if found_objects:
                    deleted_info = queryset.delete()
                    deleted_count = deleted_info[0]

            response_data = self._build_base_response_data(
                ids, missing_ids, deleted_count
            )

            return success_response(
                data=response_data,
                message=self.on_bulk_delete_message(deleted_count),
                status_code=status.HTTP_200_OK,
            )

        except ValidationError as e:
            return error_response(
                errors=e.detail,
                message="Bulk delete validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["delete"], url_path="bulk-soft-delete")
    def bulk_soft_delete(self, request: Request) -> Response:
        """
        Soft delete multiple objects in a single request using bulk operations.

        This action works with drf-common's SoftDeleteMixin by default.
        If your Model is not using the AbstractBaseModel or SoftDeleteMixin:
                Ensure your model has the necessary fields (deleted_at and is_active).
                or Override this method to implement custom soft delete logic.
        """
        ids = request.data

        try:
            self._validate_delete_ids(ids, "soft delete")

            with transaction.atomic():
                queryset, found_objects, missing_ids = self._get_queryset_data(ids)

                soft_deleted_count = 0
                if found_objects:
                    soft_deleted_count = queryset.update(
                        deleted_at=timezone.now(), is_active=False
                    )

            response_data = self._build_base_response_data(
                ids, missing_ids, soft_deleted_count
            )

            return success_response(
                data=response_data,
                message=self.on_bulk_soft_delete_message(soft_deleted_count),
                status_code=status.HTTP_200_OK,
            )

        except ValidationError as e:
            return error_response(
                errors=e.detail,
                message="Bulk soft delete validation failed",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

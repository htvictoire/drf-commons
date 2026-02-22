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

from drf_commons.common_conf import settings
from drf_commons.response.utils import error_response, success_response
from .crud import CreateModelMixin, DestroyModelMixin, UpdateModelMixin
from .utils import get_model_name


class BulkOperationMixin:
    """
    Mixin for bulk operations: create, update, delete.
    """

    bulk_batch_size = None  # Max items per bulk operation; defaults to settings

    def validate_bulk_data(self, data: List[Dict[str, Any]]) -> None:
        """Validate bulk operation data (raise-only)."""
        model_name = get_model_name(self)
        bulk_batch_size = self.get_bulk_batch_size()

        if not isinstance(data, list):
            raise ValidationError(
                f"Data must be a list of objects for {model_name}."
            )

        if not data:
            raise ValidationError(
                f"Data cannot be empty for {model_name} objects bulk operation."
            )

        if len(data) > bulk_batch_size:
            raise ValidationError(
                f"Batch size cannot exceed {bulk_batch_size} items for {model_name}."
            )

    def get_bulk_batch_size(self) -> int:
        """Resolve batch size dynamically unless explicitly overridden."""
        if self.bulk_batch_size is not None:
            return self.bulk_batch_size
        return settings.BULK_OPERATION_BATCH_SIZE


class BulkCreateModelMixin(CreateModelMixin, BulkOperationMixin):
    """
    Bulk create model instances.

    Contract: bulk create is a direct-write path and rejects nested/custom serializer fields.
    """

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

    Contract: bulk update is a direct-write path and rejects nested/custom serializer fields.
    """
    use_save_on_bulk_update = False

    def on_update_message(self):
        return super().on_update_message() + " (bulk operation)"

    @action(detail=False, methods=["put", "patch"], url_path="bulk-update")
    def bulk_update(self, request: Request, *args, **kwargs) -> Response:
        """Update multiple objects in a single request.

        PUT enforces full-update validation semantics.
        PATCH applies partial-update semantics.
        """
        try:
            self.validate_bulk_data(request.data)
            kwargs["many_on_update"] = True
            partial = request.method.upper() == "PATCH"
            with transaction.atomic():
                return self.update(request, partial=partial, *args, **kwargs)
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

    def _validate_delete_ids(self, ids, operation_name="delete"):
        """Common validation for bulk delete operations."""
        if not isinstance(ids, list):
            raise ValidationError("IDs must be provided as a list.")

        if not ids:
            raise ValidationError("IDs list cannot be empty.")

        bulk_batch_size = self.get_bulk_batch_size()
        if len(ids) > bulk_batch_size:
            raise ValidationError(
                f"Cannot {operation_name} more than {bulk_batch_size} items at once."
            )

    def _get_queryset_data(self, ids):
        """Get queryset and process found/missing IDs."""
        queryset = self.get_queryset().filter(pk__in=ids)
        found_ids = list(queryset.values_list("pk", flat=True))
        missing_ids = set(map(str, ids)) - set(map(str, found_ids))

        return queryset, found_ids, missing_ids

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
                queryset, found_ids, missing_ids = self._get_queryset_data(ids)
                deleted_count = 0
                if found_ids:
                    _, deleted_details = queryset.delete()
                    deleted_count = deleted_details.get(
                        queryset.model._meta.label, 0
                    )

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
        If your Model is not using the BaseModelMixin or SoftDeleteMixin:
                Ensure your model has the necessary fields (deleted_at and is_active).
                or Override this method to implement custom soft delete logic.
        """
        ids = request.data

        try:
            self._validate_delete_ids(ids, "soft delete")

            with transaction.atomic():
                queryset, found_ids, missing_ids = self._get_queryset_data(ids)

                soft_deleted_count = 0
                if found_ids:
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

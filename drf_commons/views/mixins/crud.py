"""
Basic CRUD operations for generic class-based views.

We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""

from rest_framework import status
from django.core.exceptions import ImproperlyConfigured
from rest_framework.exceptions import ValidationError

from drf_commons.response.utils import success_response
from .shared import BulkDirectSerializerContractMixin
from .utils import get_model_name


class CreateModelMixin(BulkDirectSerializerContractMixin):
    """
    Create a model instance.
    """

    return_data_on_create = False

    def on_create_message(self):
        return f"{get_model_name(self)} created successfully"

    def create(self, request, *args, **kwargs):
        many_on_create = kwargs.get("many_on_create", False)
        serializer = self.get_serializer(data=request.data, many=many_on_create)
        if many_on_create:
            self._validate_bulk_direct_serializer_contract(serializer, "create")
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        if self.return_data_on_create:
            return success_response(
                data=serializer.data,
                message=self.on_create_message(),
                status_code=status.HTTP_201_CREATED,
            )
        return success_response(
            message=self.on_create_message(),
            status_code=status.HTTP_201_CREATED,
        )

    def perform_create(self, serializer):
        serializer.save()


class ListModelMixin:
    """
    List a queryset.
    """

    append_indexes = True

    def on_list_message(self):
        return f"{get_model_name(self)} retrieved successfully"

    def _add_indexes_to_results(self, results):
        """Add sequential index to each item in results."""
        if not self.append_indexes:
            return results

        return [{**item, "index": idx} for idx, item in enumerate(results, 1)]

    def list(self, request, *args, **kwargs):
        paginated = request.query_params.get("paginated", "true").lower() in [
            "true",
            "1",
            "yes",
        ]
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset) if paginated else None

        if page is not None and paginated:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)
            if "results" in paginated_response.data:
                paginated_response.data["results"] = self._add_indexes_to_results(
                    paginated_response.data["results"]
                )
            return success_response(
                data=paginated_response.data,
                message=self.on_list_message(),
            )

        serializer = self.get_serializer(queryset, many=True)
        results = self._add_indexes_to_results(serializer.data)
        return success_response(
            data={
                "next": None,
                "previous": None,
                "count": len(results),
                "results": results,
            },
            message=self.on_list_message(),
        )


class RetrieveModelMixin:
    """
    Retrieve a model instance.
    """

    def on_retrieve_message(self):
        return f"{get_model_name(self)} retrieved successfully"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success_response(
            data=serializer.data,
            message=self.on_retrieve_message(),
        )


class UpdateModelMixin(BulkDirectSerializerContractMixin):
    """
    Update a model instance.
    """

    return_data_on_update = False

    def on_update_message(self):
        return f"{get_model_name(self)} updated successfully"

    def _resolve_bulk_update_instances(self, payload):
        """Resolve bulk update instances in the exact request-row order."""
        if not isinstance(payload, list):
            raise ValidationError("Bulk update payload must be a list of objects.")

        if not payload:
            raise ValidationError("Bulk update payload cannot be empty.")

        requested_ids = []
        seen_ids = set()

        for index, item in enumerate(payload):
            row_number = index + 1
            if not isinstance(item, dict):
                raise ValidationError(
                    {index: f"Row {row_number} must be an object containing an 'id'."}
                )

            if "id" not in item or item.get("id") in (None, ""):
                raise ValidationError(
                    {index: f"Row {row_number} is missing required field 'id'."}
                )

            row_id = item.get("id")
            normalized_id = str(row_id)
            if normalized_id in seen_ids:
                raise ValidationError(
                    {index: f"Duplicate id '{row_id}' at row {row_number}."}
                )
            seen_ids.add(normalized_id)
            requested_ids.append(row_id)

        instances = list(self.get_queryset().filter(pk__in=requested_ids))
        instance_by_id = {str(obj.pk): obj for obj in instances}

        missing_ids = [
            row_id for row_id in requested_ids if str(row_id) not in instance_by_id
        ]
        if missing_ids:
            raise ValidationError(
                {
                    "id": (
                        "Some rows reference objects that do not exist or are not "
                        f"accessible in this queryset: {missing_ids}"
                    )
                }
            )

        return [instance_by_id[str(item["id"])] for item in payload]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        if kwargs.get("many_on_update", False):
            instances = self._resolve_bulk_update_instances(request.data)
            serializer = self.get_serializer(
                instances, data=request.data, partial=partial, many=True
            )
            self._validate_bulk_direct_serializer_contract(serializer, "update")
        else:
            # For single updates, get instance from URL
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if self.return_data_on_update:
            return success_response(
                data=serializer.data,
                message=self.on_update_message(),
            )
        return success_response(
            message=self.on_update_message(),
        )

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class DestroyModelMixin:
    """
    Destroy a model instance.
    """

    def on_destroy_message(self):
        return f"{get_model_name(self)} deleted successfully"

    def on_soft_destroy_message(self):
        return self.on_destroy_message()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(message=self.on_destroy_message())

    def soft_destroy(self, request, *args, **kwargs):
        """
        This action works with drf-common's SoftDeleteMixin by default.
        If your Model is not using the BaseModelMixin or SoftDeleteMixin:
            Override this method to implement soft delete logic.
        """
        instance = self.get_object()
        self.perform_soft_destroy(instance)
        return success_response(message=self.on_soft_destroy_message())

    def perform_destroy(self, instance):
        instance.delete()

    def perform_soft_destroy(self, instance):
        if not hasattr(instance, "soft_delete") or not callable(instance.soft_delete):
            raise ImproperlyConfigured(
                f"Soft delete is not supported for {get_model_name(self)}"
            )
        instance.soft_delete()

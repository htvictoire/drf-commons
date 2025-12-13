"""
Basic CRUD operations for generic class-based views.

We don't bind behaviour to http method handlers yet,
which allows mixin classes to be composed in interesting ways.
"""

from rest_framework import status
from rest_framework.exceptions import ValidationError

from drf_commons.response.utils import success_response
from .utils import get_model_name


class CreateModelMixin:
    """
    Create a model instance.
    """

    return_data_on_create = False

    def on_create_message(self):
        return f"{get_model_name(self)} created successfully"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=kwargs.get("many_on_create", False))
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

        results_with_index = []
        for idx, item in enumerate(results, 1):
            item["index"] = idx
            results_with_index.append(item)
        return results_with_index

    def list(self, request, *args, **kwargs):
        paginated = request.query_params.get("paginated", "true").lower() in [
            "true",
            "1",
            "yes",
        ]
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

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
                "count": queryset.count(),
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


class UpdateModelMixin:
    """
    Update a model instance.
    """

    return_data_on_update = False
    def on_update_message(self):
        return f"{get_model_name(self)} updated successfully"

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        if kwargs.get("many_on_update", False):
            # For bulk updates, get instances based on IDs in request data
            ids = [item.get('id') for item in request.data if item.get('id')]
            instances = list(self.get_queryset().filter(pk__in=ids))
            serializer = self.get_serializer(
                instances, data=request.data, partial=partial, many=True
            )
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
        return success_response(
            message=self.on_destroy_message(),
            status_code=status.HTTP_204_NO_CONTENT,
        )

    def soft_destroy(self, request, *args, **kwargs):
        """
        This action works with drf-common's SoftDeleteMixin by default.
        If your Model is not using the BaseModelMixin or SoftDeleteMixin:
            Override this method to implement soft delete logic.
        """
        instance = self.get_object()
        try:
            self.perform_soft_destroy(instance)
        except AttributeError:
            raise ValidationError(
                f"Soft delete is not supported for {instance.__class__.__name__} model"
            )
        return success_response(
            message=self.on_soft_destroy_message(),
            status_code=status.HTTP_204_NO_CONTENT,
        )

    def perform_destroy(self, instance):
        instance.delete()

    def perform_soft_destroy(self, instance):
        instance.soft_delete()

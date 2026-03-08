Extensibility
=============

Every component in drf-commons is designed for extension. This page documents
the primary extension patterns.

Custom ViewSet Compositions
---------------------------

Pre-composed ViewSet classes cover the most common patterns. For unusual
requirements, compose directly from the mixin layer:

.. code-block:: python

   from rest_framework.viewsets import GenericViewSet
   from drf_commons.views.mixins import (
       ListModelMixin,
       RetrieveModelMixin,
       BulkCreateModelMixin,
       BulkDeleteModelMixin,
       FileExportMixin,
   )

   class AuditableAppendOnlyViewSet(
       ListModelMixin,
       RetrieveModelMixin,
       BulkCreateModelMixin,
       BulkDeleteModelMixin,
       FileExportMixin,
       GenericViewSet,
   ):
       """
       Records can be listed, retrieved, bulk-created, and bulk-deleted,
       but not individually created or updated.
       """
       pass

Adding Custom Actions
~~~~~~~~~~~~~~~~~~~~~

DRF's ``@action`` decorator works normally on drf-commons ViewSets:

.. code-block:: python

   from rest_framework.decorators import action
   from drf_commons.response import success_response
   from drf_commons.views import BaseViewSet

   class ArticleViewSet(BaseViewSet):
       @action(detail=True, methods=["post"], url_path="publish")
       def publish(self, request, pk=None):
           article = self.get_object()
           article.published = True
           article.save()
           return success_response(
               data=self.get_serializer(article).data,
               message="Article published.",
           )

Extending Model Mixins
----------------------

Subclass any mixin to extend or override behavior:

.. code-block:: python

   from drf_commons.models.base import SoftDeleteMixin

   class CascadingSoftDeleteMixin(SoftDeleteMixin):
       """
       Extends SoftDeleteMixin to cascade soft deletes to related objects.
       """
       # Override in concrete model to specify related managers to cascade
       soft_delete_related = []

       def soft_delete(self):
           for related_manager_name in self.soft_delete_related:
               manager = getattr(self, related_manager_name)
               for obj in manager.filter(is_active=True):
                   obj.soft_delete()
           super().soft_delete()

Custom Serializer Fields
------------------------

The configurable field system is extensible. All field types are built on
:class:`~drf_commons.serializers.fields.base.ConfigurableRelatedField`.
Implement a custom field by providing the input parsing and output transformation:

.. code-block:: python

   from drf_commons.serializers.fields.base import ConfigurableRelatedField

   class SlugToDataField(ConfigurableRelatedField):
       """
       Accept a slug string on write, return nested serializer data on read.
       """

       def to_internal_value(self, data: str):
           """Resolve slug to model instance."""
           try:
               return self.get_queryset().get(slug=data)
           except self.get_queryset().model.DoesNotExist:
               self.fail("does_not_exist", pk_value=data)

       def to_representation(self, value):
           """Serialize instance using the configured serializer."""
           if isinstance(value, dict):
               return value
           serializer = self.serializer_class(value, context=self.context)
           return serializer.data

   # Usage:
   class ArticleSerializer(BaseModelSerializer):
       category = SlugToDataField(
           queryset=Category.objects.all(),
           serializer=CategorySerializer,
       )

Custom Response Envelope
------------------------

If your project requires a different envelope structure, override the utility
functions in your own module:

.. code-block:: python

   # myapp/response.py
   from datetime import datetime, timezone
   from rest_framework.response import Response

   def success_response(data=None, message="", status_code=200, **kwargs):
       return Response(
           {
               "ok": True,
               "ts": datetime.now(timezone.utc).isoformat(),
               "msg": message,
               "payload": data,
               **kwargs,
           },
           status=status_code,
       )

Then import from ``myapp.response`` rather than ``drf_commons.response``
throughout your project.

If you want to customize only specific ViewSet responses, override the mixin
methods:

.. code-block:: python

   from drf_commons.views.mixins import ListModelMixin
   from myapp.response import success_response

   class CustomListMixin(ListModelMixin):
       def list(self, request, *args, **kwargs):
           response = super().list(request, *args, **kwargs)
           response.data["_api_version"] = "v2"
           return response

Custom Pagination
-----------------

.. code-block:: python

   from drf_commons.pagination import StandardPageNumberPagination

   class TinyPagePagination(StandardPageNumberPagination):
       page_size = 5
       max_page_size = 20

   class LargeDataViewSet(BaseViewSet):
       pagination_class = TinyPagePagination

Custom Settings
---------------

Extend the default settings by reading from ``COMMON`` with custom keys:

.. code-block:: python

   # myapp/conf.py
   from drf_commons.common_conf.settings import CommonSettings

   class AppSettings(CommonSettings):
       @property
       def RATE_LIMIT_PER_MINUTE(self):
           return self._get("RATE_LIMIT_PER_MINUTE", default=60)

       @property
       def ENABLE_WEBHOOKS(self):
           return self._get("ENABLE_WEBHOOKS", default=False)

   app_settings = AppSettings()

   # settings.py
   COMMON = {
       "RATE_LIMIT_PER_MINUTE": 120,
       "ENABLE_WEBHOOKS": True,
   }

Extending the Import Pipeline
------------------------------

The import pipeline can be extended through:

1. **Transforms**: Per-field data transformation functions (see :doc:`services`)
2. **Progress callbacks**: For monitoring long-running imports
3. **Custom FileReader**: For non-standard file formats (internal API)

For deeply custom import logic, extend ``FileImportService`` directly and
override the processing stages:

.. code-block:: python

   from drf_commons.services.import_from_file import FileImportService

   class ValidatingImportService(FileImportService):
       def _validate_row(self, model_key, row):
           # Custom cross-row validation logic
           super()._validate_row(model_key, row)
           if model_key == "employee" and not row.get("department_code"):
               raise ValueError("Employee row missing department_code")

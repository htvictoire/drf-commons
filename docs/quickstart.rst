Quick Start
===========

Install and configure
---------------------

.. code-block:: python

   INSTALLED_APPS = [
       "drf_commons",
   ]

   MIDDLEWARE = [
       # ...
       "drf_commons.middlewares.current_user.CurrentUserMiddleware",
       "drf_commons.middlewares.debug.DebugMiddleware",
   ]

Model + serializer + viewset
----------------------------

.. code-block:: python

   from drf_commons.models.base import BaseModelMixin
   from drf_commons.serializers.base import BaseModelSerializer
   from drf_commons.views.base import BulkViewSet

   class Item(BaseModelMixin):
       name = models.CharField(max_length=120)

   class ItemSerializer(BaseModelSerializer):
       class Meta(BaseModelSerializer.Meta):
           model = Item
           fields = "__all__"

``BaseModelSerializer`` is required if you use configurable related fields with nested
input, because deferred relation writes are executed during serializer ``save()``.

   class ItemViewSet(BulkViewSet):
       queryset = Item.objects.all()
       serializer_class = ItemSerializer

Response helpers
----------------

.. code-block:: python

   from drf_commons.response import success_response, error_response

   return success_response(data={"id": 1}, message="Created")
   return error_response(message="Invalid input", errors={"field": ["required"]})

File import/export
------------------

``FileImportMixin`` and ``FileExportMixin`` can be composed into viewsets for import/export endpoints.
See ``docs/modules/services.rst`` and ``docs/modules/views.rst`` for full configuration and endpoint behavior.

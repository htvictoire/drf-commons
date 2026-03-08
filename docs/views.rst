Views
=====

drf-commons provides a complete set of pre-composed ViewSet classes and the
action mixins from which they are built. Every ViewSet class is a transparent
composition of mixins — no hidden behavior, no magic dispatch.

Pre-Composed ViewSets
---------------------

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Class
     - Provided Actions
   * - ``BaseViewSet``
     - CRUD + file export
   * - ``BulkViewSet``
     - CRUD + bulk create/update/delete + file export
   * - ``ReadOnlyViewSet``
     - List + retrieve + file export
   * - ``CreateListViewSet``
     - Create + list + file export
   * - ``BulkCreateViewSet``
     - Bulk create only
   * - ``BulkUpdateViewSet``
     - Bulk update only
   * - ``BulkDeleteViewSet``
     - Bulk delete only
   * - ``BulkOnlyViewSet``
     - Bulk create + update + delete
   * - ``ImportableViewSet``
     - CRUD + file import + file export
   * - ``BulkImportableViewSet``
     - CRUD + bulk ops + file import + file export

Import:

.. code-block:: python

   from drf_commons.views import (
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

CRUD Mixins
-----------

CreateModelMixin
~~~~~~~~~~~~~~~~

Handles ``POST /resource/`` for single-object creation.

**Configuration**:

.. code-block:: python

   class MyViewSet(BaseViewSet):
       return_data_on_create = True  # Default: True
       # If False, returns empty data on 201. Reduces response payload.

**Response**: ``HTTP 201`` with the serialized created object or empty data.

ListModelMixin
~~~~~~~~~~~~~~

Handles ``GET /resource/`` for listing objects.

**Pagination control**:

The list action respects the ``paginated`` query parameter:

.. code-block:: text

   GET /articles/?paginated=true   — paginated results
   GET /articles/?paginated=false  — all results (use with caution)
   GET /articles/                  — uses ViewSet default

**Index appending**:

When ``append_indexes = True`` (default on most ViewSets), each result object
receives a sequential ``index`` field:

.. code-block:: json

   {"id": "...", "title": "...", "index": 1}

This is useful for client-side display ordering.

**Configuration**:

.. code-block:: python

   class MyViewSet(BaseViewSet):
       append_indexes = True      # Default: True
       pagination_class = StandardPageNumberPagination

RetrieveModelMixin
~~~~~~~~~~~~~~~~~~

Handles ``GET /resource/{id}/``.

Returns standardized success response with the serialized object.

UpdateModelMixin
~~~~~~~~~~~~~~~~

Handles ``PUT /resource/{id}/`` (full update) and ``PATCH /resource/{id}/``
(partial update).

**Configuration**:

.. code-block:: python

   class MyViewSet(BaseViewSet):
       return_data_on_update = True  # Default: True
       # If False, returns empty data on 200.

DestroyModelMixin
~~~~~~~~~~~~~~~~~

Handles ``DELETE /resource/{id}/``.

Returns ``HTTP 204`` with standardized success response.

.. code-block:: python

   class MyViewSet(BaseViewSet):
       def perform_destroy(self, instance):
           # Override for soft delete:
           instance.soft_delete()

Bulk Operation Mixins
---------------------

BulkCreateModelMixin
~~~~~~~~~~~~~~~~~~~~

Provides ``POST /resource/bulk-create/``.

* Accepts a JSON array of objects
* Validates array format and size against ``BULK_OPERATION_BATCH_SIZE``
* Wraps in ``transaction.atomic()``
* Returns ``HTTP 201`` with created objects (or count if ``return_data_on_create=False``)

.. code-block:: python

   # POST /articles/bulk-create/
   # Body:
   [
     {"title": "Article 1", "content": "..."},
     {"title": "Article 2", "content": "..."}
   ]

BulkUpdateModelMixin
~~~~~~~~~~~~~~~~~~~~

Provides ``PUT /resource/bulk-update/`` and ``PATCH /resource/bulk-update/``.

* ``PUT`` validates all fields (full update)
* ``PATCH`` uses partial update semantics
* Accepts a JSON array with ``id`` field in each object
* Instance count must exactly match incoming data count

**Bulk update mode** (default, ``use_save_on_bulk_update = False``):

Issues a single ``bulk_update()`` SQL statement. Audit fields auto-populated.

**Save mode** (``use_save_on_bulk_update = True``):

Calls ``instance.save()`` for each object. Triggers signals.

.. code-block:: python

   class ProductViewSet(BulkViewSet):
       use_save_on_bulk_update = False  # default
       bulk_batch_size = 500           # override global setting

.. code-block:: python

   # PATCH /products/bulk-update/
   [
     {"id": "uuid-1", "price": "29.99"},
     {"id": "uuid-2", "price": "49.99"}
   ]

BulkDeleteModelMixin
~~~~~~~~~~~~~~~~~~~~

Provides:

* ``DELETE /resource/bulk-delete/`` — Hard delete
* ``DELETE /resource/bulk-soft-delete/`` — Soft delete (requires ``SoftDeleteMixin``)

Accepts a JSON array of IDs. Returns a detailed deletion report:

.. code-block:: json

   {
     "success": true,
     "data": {
       "requested_count": 10,
       "count": 8,
       "missing_ids": ["uuid-3", "uuid-7"]
     }
   }

Import/Export Mixins
--------------------

FileExportMixin
~~~~~~~~~~~~~~~

Provides ``POST /resource/export/``.

**Request body**:

.. code-block:: json

   {
     "file_type": "xlsx",
     "includes": ["title", "status", "created_at"],
     "column_config": {
       "title": {"width": 40, "header": "Article Title"}
     },
     "data": []
   }

**Supported file types**: ``csv``, ``xlsx``, ``pdf``

Returns an ``HttpResponse`` with the file as an attachment.

**ViewSet configuration**:

.. code-block:: python

   class ArticleViewSet(BaseViewSet):
       export_field_config = {
           "title": "Title",
           "published": "Published",
           "created_at": "Created At",
       }

FileImportMixin
~~~~~~~~~~~~~~~

Provides ``POST /resource/import-from-file/``.

**Request**: ``multipart/form-data`` with:

* ``file`` — CSV, XLS, or XLSX file
* ``append_data`` — ``true`` to merge with existing, ``false`` to replace

**ViewSet configuration**:

.. code-block:: python

   class EmployeeViewSet(ImportableViewSet):
       import_file_config = {
           "file_format": "xlsx",
           "order": ["department", "employee"],
           "models": {
               "department": {
                   "model": Department,
                   "fields": ["name", "code"],
                   "unique_fields": ["code"],
               },
               "employee": {
                   "model": Employee,
                   "fields": ["first_name", "last_name", "email"],
                   "unique_fields": ["email"],
               },
           },
       }

       # Optional: transform imported values
       import_transforms = {
           "email": lambda v: v.strip().lower(),
       }

See :doc:`services` for the full import configuration reference.

Custom ViewSet Composition
--------------------------

When no pre-composed ViewSet matches your requirements, compose exactly what
you need:

.. code-block:: python

   from rest_framework.viewsets import GenericViewSet
   from drf_commons.views.mixins import (
       ListModelMixin,
       BulkCreateModelMixin,
       FileExportMixin,
   )

   class AppendOnlyViewSet(
       ListModelMixin,
       BulkCreateModelMixin,
       FileExportMixin,
       GenericViewSet,
   ):
       """
       A resource that allows listing, bulk creation, and export,
       but not individual create, update, or delete.
       """
       queryset = LogEntry.objects.all()
       serializer_class = LogEntrySerializer

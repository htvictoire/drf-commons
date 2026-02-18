views
=====

This page documents behavior from:

- ``drf_commons/views/mixins/crud.py``
- ``drf_commons/views/mixins/bulk.py``
- ``drf_commons/views/mixins/import_export.py``
- ``drf_commons/views/base.py``
- ``drf_commons/views/mixins/utils.py``

Design Intent
-------------

DRF gives low-level mixins and ``ModelViewSet`` defaults, but many teams still repeat:

- response-envelope boilerplate,
- batch endpoint wiring,
- import/export action mechanics,
- consistent success/error message patterns.

``drf-commons`` view mixins provide composable endpoint behavior with a shared response envelope.

CRUD Mixins
-----------

``CreateModelMixin``
^^^^^^^^^^^^^^^^^^^^

Default DRF behavior

- DRF create usually returns serializer data by default in ``CreateModelMixin`` patterns.

This implementation

- validates serializer,
- calls ``perform_create(serializer)``,
- returns ``success_response`` with 201,
- response body is message-only unless ``return_data_on_create = True``.

Production trade-off

Message-only responses reduce payload size but can break clients expecting created object content.

``ListModelMixin``
^^^^^^^^^^^^^^^^^^

Behavioral contract

- reads query param ``paginated`` and treats ``true/1/yes`` as true,
- always obtains ``queryset = self.filter_queryset(self.get_queryset())``,
- calls ``page = self.paginate_queryset(queryset)`` only when ``paginated`` is true,
- if ``page is not None`` and ``paginated`` true: returns paginated data,
- otherwise returns full result with ``next=None`` and ``previous=None`` envelope,
- optional ``index`` injection per item when ``append_indexes=True``.

Edge cases

- disabling pagination with ``?paginated=false`` bypasses paginator internals.
- non-paginated path derives ``count`` from serialized results and avoids a separate ``queryset.count()`` query.
- index injection mutates serialized item dicts.

Performance notes

- disabling pagination (``?paginated=false``) on large datasets can cause high memory usage because the full result set is serialized in one response.
- index generation is O(n) Python-side and negligible compared to DB/serialization cost.

``RetrieveModelMixin``
^^^^^^^^^^^^^^^^^^^^^^

Thin wrapper around ``get_object()`` + serializer + ``success_response``.

``UpdateModelMixin``
^^^^^^^^^^^^^^^^^^^^

Single update path

- standard ``get_object()`` then serializer update.

Bulk update path (``many_on_update=True``)

- validates each row is an object containing non-empty ``id``,
- rejects duplicate IDs in the same request,
- fetches instances by ``pk__in`` and builds an ``id -> instance`` map,
- rejects requests that reference missing/inaccessible IDs,
- reconstructs instance list in request-row order,
- passes aligned instances and request data into serializer with ``many=True``.

Safety contract

The serializer update step is positional, but inputs are pre-aligned by explicit ID mapping in the view mixin. Queryset ordering no longer controls row-to-instance matching.

``DestroyModelMixin``
^^^^^^^^^^^^^^^^^^^^^

- ``destroy`` calls ``instance.delete()`` and returns 204 envelope.
- ``soft_destroy`` calls ``instance.soft_delete()`` and returns 204 envelope.
- if model lacks ``soft_delete``, raises DRF ``ValidationError``.

HTTP semantics note

This implementation returns a response body with status 204. Some clients/proxies expect empty body for 204.


Bulk Mixins
-----------

Problem addressed
^^^^^^^^^^^^^^^^^

DRF does not standardize bulk create/update/delete endpoint contracts.

``BulkOperationMixin``
^^^^^^^^^^^^^^^^^^^^^^

``validate_bulk_data`` enforces:

- payload must be non-empty,
- payload must be list,
- length <= ``bulk_batch_size``.

``bulk_batch_size`` defaults to ``COMMON_BULK_OPERATION_BATCH_SIZE`` (or unprefixed setting fallback) through ``common_conf.settings``.

``BulkCreateModelMixin``
^^^^^^^^^^^^^^^^^^^^^^^^

- action: ``POST /bulk-create``
- validates list payload,
- enforces direct bulk serializer contract,
  nested serializer fields and ``drf_commons`` configurable related fields are rejected,
- runs create path in atomic transaction,
- on validation error returns structured 400 error response.

``BulkUpdateModelMixin``
^^^^^^^^^^^^^^^^^^^^^^^^

- action: ``PUT /bulk-update`` and ``PATCH /bulk-update``
- validates list payload,
- enforces direct bulk serializer contract,
  nested serializer fields and ``drf_commons`` configurable related fields are rejected,
- calls ``update(..., many_on_update=True)`` in transaction,
- ``PUT`` executes full-update validation semantics (``partial=False``),
- ``PATCH`` executes partial-update semantics (``partial=True``),
- catches validation error into structured 400 response.

``BulkDeleteModelMixin``
^^^^^^^^^^^^^^^^^^^^^^^^

- action: ``DELETE /bulk-delete`` expects request body as list of IDs,
- validates ID list,
- fetches existing objects, computes missing IDs,
- executes queryset ``delete()`` and reports direct target-row count,
- response includes ``requested_count``, ``missing_ids``, ``missing_count``, ``count``.

``bulk-soft-delete``
^^^^^^^^^^^^^^^^^^^^

- action: ``DELETE /bulk-soft-delete``
- uses queryset ``update(deleted_at=now, is_active=False)``.

Permissions responsibility
^^^^^^^^^^^^^^^^^^^^^^^^^^

Bulk actions are direct queryset operations. Object-level permission enforcement
for bulk create/update/delete is the integrator's responsibility.

- ensure queryset scoping already reflects allowed objects for the caller
- if per-object checks are required, override bulk actions and call
  ``check_object_permissions(request, obj)`` for each target object before mutation

Trade-off

Fast and query-efficient, but bypasses model ``save()`` hooks/signals and any ``UserActionMixin`` attribution logic.


File Import Mixin
-----------------

Problem it solves
^^^^^^^^^^^^^^^^^

File import endpoints are usually custom and inconsistent across projects (validation, partial failure reporting, template generation, replace-vs-append behavior).

Endpoint contracts
^^^^^^^^^^^^^^^^^^

``POST /import-from-file``

Required:

- multipart file field ``file``
- exactly one of ``append_data`` or ``replace_data`` must resolve to ``true``
- accepted boolean inputs for each flag: ``bool``, ``0/1``, and strings ``true/false``, ``yes/no``, ``on/off``

``GET /download-import-template``

- returns static template file,
- generates file via management command if missing.

How default DRF is insufficient
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

DRF parsers and serializers do not provide a configurable multi-model tabular import pipeline with strict template validation and row-level summaries.

Implementation flow for ``import_file``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. asserts ``import_file_config`` and ``import_template_name`` on viewset,
2. validates payload mode and uploaded file,
3. builds ``FileImportService`` with optional transforms and progress callback,
   note: ``FileImportService`` is imported inside this action, so missing import dependencies surface at endpoint runtime, not at Django startup,
4. executes import with mode-specific transaction semantics:

   - ``append_data`` true: import runs directly and returns summary,
   - ``replace_data`` true: delete + import run in one transaction.
     Any failed rows roll back the transaction and preserve existing dataset.

5. truncates returned failed rows to ``IMPORT_FAILED_ROWS_DISPLAY_LIMIT``,
6. status code rules:

   - append mode:
     - 201: no failed rows,
     - 207: mixed success/failure,
     - 422: all failed.
   - replace mode:
     - 201: full import success and replacement committed,
     - 422: any failed rows; replacement rolled back.

Failure handling behavior
^^^^^^^^^^^^^^^^^^^^^^^^^

- catches ``ImportValidationError`` and returns structured 422 responses,
- detects header/template errors by substring match on exception text,
- unhandled non-validation exceptions propagate to DRF exception handler.

Replace mode contract
^^^^^^^^^^^^^^^^^^^^^

``replace_data`` true is strict all-or-nothing replacement:

- existing queryset rows are replaced only when imported rows have zero failures,
- if any row fails, no replacement is committed,
- response includes failure summary and limited failed-row details.

Integration guidance
^^^^^^^^^^^^^^^^^^^^

Use replace mode when the endpoint contract requires deterministic dataset replacement.


File Export Mixin
-----------------

Problem it solves
^^^^^^^^^^^^^^^^^

Frontend export UIs commonly need server-generated CSV/XLSX/PDF with consistent column labels and optional document metadata.

Endpoint contract
^^^^^^^^^^^^^^^^^

``POST /export-as-file`` expects:

- ``file_type``: ``pdf`` | ``xlsx`` | ``csv``
- ``includes``: selected fields as list or comma-separated string
- ``column_config``: label/alignment/common-field metadata
- ``data``: array of rows to export
- optional ``file_titles``

Internal behavior
^^^^^^^^^^^^^^^^^

- validates type, includes, data,
- normalizes ``includes`` to a non-empty ordered field list,
- delegates processing/export to ``ExportService``,
- filename derived from slugified model display name.

Known contract caveats from code
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- empty list ``data=[]`` is treated as missing data and rejected.

When not to use this mixin
^^^^^^^^^^^^^^^^^^^^^^^^^^

- when exported data must be derived server-side from secure queryset only (not client-provided rows),
- when strict schema validation of export payload is required before formatting.

Alternatives
^^^^^^^^^^^^

- dedicated export endpoints that ignore client ``data`` and stream queryset results,
- asynchronous export jobs for very large datasets.


Composed ViewSets
-----------------

``views/base.py`` combines mixins into presets:

- ``BaseViewSet``: CRUD + file export
- ``BulkViewSet``: Base + bulk create/update/delete
- ``ReadOnlyViewSet``: list/retrieve + file export
- ``CreateListViewSet``: create/list + file export
- ``BulkCreateViewSet`` / ``BulkUpdateViewSet`` / ``BulkDeleteViewSet`` / ``BulkOnlyViewSet``
- ``ImportableViewSet`` and ``BulkImportableViewSet`` add file import endpoints

These classes are composition conveniences, not new runtime frameworks.

Real production example
-----------------------

.. code-block:: python

   from rest_framework import filters
   from drf_commons.views.base import BulkImportableViewSet
   from drf_commons.filters.ordering.computed import ComputedOrderingFilter
   from drf_commons.pagination.base import StandardPageNumberPagination
   from inventory.models import StockItem
   from inventory.serializers import StockItemSerializer

   class StockItemViewSet(BulkImportableViewSet):
       queryset = StockItem.objects.filter(is_active=True).select_related("category")
       serializer_class = StockItemSerializer
       pagination_class = StandardPageNumberPagination
       filter_backends = [ComputedOrderingFilter, filters.SearchFilter]
       ordering_fields = ["sku", "name", "category", "updated_at"]
       computed_ordering_fields = {
           "category": "category__name",
       }

       import_template_name = "stock_items_template.xlsx"
       import_file_config = {
           "file_format": "xlsx",
           "order": ["main"],
           "models": {
               "main": {
                   "model": "inventory.StockItem",
                   "unique_by": ["sku"],
                   "update_if_exists": True,
                   "direct_columns": {
                       "sku": "SKU",
                       "name": "Name",
                       "quantity": "Quantity",
                   },
                   "required_fields": ["sku", "name"],
               }
           },
       }

       import_transforms = {
           "normalize_sku": lambda v: str(v).strip().upper(),
       }

``import_transforms`` is optional; when omitted, import runs with an empty transform map.


Compatibility concerns
----------------------

- Requires DRF action routing (``@action`` endpoints).
- File import requires ``pandas`` and Excel engines for Excel modes.
- File export to XLSX/PDF requires optional dependencies.
- Replace mode and bulk soft delete behavior should be aligned with your domain audit rules.

Migration strategy
------------------

1. Introduce response-envelope mixins first on low-risk endpoints.
2. Add bulk endpoints behind permission flags.
3. Introduce import/export endpoints only after defining operational runbooks.
4. For existing APIs, keep old endpoints during transition; expose new mixin endpoints with explicit versioning.

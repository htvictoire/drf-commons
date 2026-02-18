services
========

This page documents production behavior from source code in:

- ``drf_commons/services/export_file/*``
- ``drf_commons/services/import_from_file/*``
- ``drf_commons/services/management/commands/generate_import_template.py``

Service Layer Scope
-------------------

DRF gives serializer/view abstractions, but file import/export workflows typically require:

- multi-step validation beyond serializer shape checks,
- optional dependencies and fallback behavior,
- output-format specific rendering concerns,
- operational controls (batch size, strict header contracts, reporting).

The ``services`` package provides those workflows as explicit service objects.

Dependency loading semantics (exact)
------------------------------------

- ``ExportService`` itself is import-safe on base install.
- CSV exporter has no optional third-party dependency.
- XLSX exporter imports ``openpyxl`` inside ``XLSXExporter.export(...)``.
- PDF exporter imports ``weasyprint`` inside ``PDFExporter.export(...)``.
- ``FileImportService`` requires ``pandas`` at module import time.
- ``FileImportMixin.import_file`` imports ``FileImportService`` inside the action method, so application startup is unaffected until import endpoint usage.
- ``generate_import_template`` command module imports ``pandas`` and ``openpyxl``; command usage therefore requires import dependencies.
- Export header integration with ``django-constance`` is optional; failures in constance import/backend initialization fall back to empty document header.

Export Service
--------------

Problem it solves
^^^^^^^^^^^^^^^^^

Producing CSV/XLSX/PDF from front-end-selected columns with shared formatting metadata usually leads to duplicated per-view logic.

Default DRF behavior
^^^^^^^^^^^^^^^^^^^^

DRF does not provide a document export engine. You manually build responses, serializers, and format-specific renderers.

How ``ExportService`` works
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``ExportService`` (``export_file/service.py``):

- lazy-loads exporters by type (``csv``, ``xlsx``, ``pdf``),
- caches exporter instances in ``self._exporters``,
- delegates payload normalization to ``process_export_data``.

Internal mechanics
^^^^^^^^^^^^^^^^^^

``process_export_data`` performs:

1. field extraction for each row using ``extract_nested_value`` (dot-path aware),
2. common-value detection for fields marked ``can_be_common`` in ``column_config``,
3. removal of common columns from table payload,
4. header assembly from constance ``DEFAULT_DOCS_HEADER`` plus common values,
5. document title normalization (trim, drop empty).

Common-value algorithm details
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A field is moved out of table into header only if:

- ``column_config[field]["can_be_common"]`` is true,
- all rows have non-empty value,
- all values are identical after string conversion.

This reduces table width for strongly uniform columns (for example, same organization or reporting period across all rows).

Format-specific exporters
-------------------------

Spreadsheet safety contract
^^^^^^^^^^^^^^^^^^^^^^^^^^^

CSV and XLSX exporters sanitize string cell values before writing:

- if first non-whitespace character is one of ``=``, ``+``, ``-``, ``@``,
  the value is prefixed with a single quote,
- applies to document headers, titles, column labels, and row data cells.

This ensures exported spreadsheets open as data-only content rather than formula execution surfaces.

CSV exporter
^^^^^^^^^^^^

Behavior:

- writes document headers at top-left,
- inserts spacing rows,
- writes centered titles as single-cell rows,
- writes column labels,
- writes data values as strings,
- appends footer ``Date: <working_date>``.

Edge case:

If ``data_rows`` is empty, exporter returns an empty CSV response body (no headers/titles/footer written).

XLSX exporter
^^^^^^^^^^^^^

Behavior:

- imports ``openpyxl`` lazily,
- styles header row with configured color,
- writes document headers and titles,
- merges title cells across columns,
- applies per-column alignment from ``column_config.align``,
- optionally auto-sizes column width with max cap,
- appends footer date in last included column.

Performance and compatibility caveats:

- title merge uses ``openpyxl.utils.get_column_letter`` and supports wide column ranges correctly.
- large exports are memory-bound because workbook is built in memory.

PDF exporter
^^^^^^^^^^^^

Behavior:

- imports ``weasyprint`` lazily,
- determines orientation with content-width heuristic,
- renders HTML template ``exports/pdf_template.html`` with context,
- generates PDF bytes via ``HTML(...).write_pdf()``.

Orientation heuristic internals:

- estimates row width from max(header_len, value_len) per column,
- converts char count to points using ``EXPORTED_DOCS_PDF_AVG_CHAR_WIDTH``,
- row is problematic if width > portrait_available_width * 1.3,
- switches to landscape when problematic-row percentage >= ``EXPORTED_DOCS_PDF_ROW_THRESHOLD_PERCENTAGE``.

Trade-offs:

- deterministic and configurable,
- still heuristic; font metrics and language character width variance can mispredict.

When not to use current export service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Avoid for very large datasets requiring streaming. Current implementation expects full data rows in memory.

Alternatives
^^^^^^^^^^^^

- queryset streaming for CSV,
- asynchronous job + object storage artifact for XLSX/PDF,
- report engine with pagination, chunking, and background rendering.


Import Service
--------------

Problem it solves
^^^^^^^^^^^^^^^^^

DRF serializers alone do not provide a robust multi-model tabular import orchestration engine with strict templates, transforms, row-level errors, and bulk persistence strategies.

Top-level flow
^^^^^^^^^^^^^^

``FileImportService.import_file(file_obj)``:

1. reads file through ``FileReader`` based on configured format,
2. determines chunk strategy from ``config.get("chunk_size", len(df))``,
3. processes full frame or chunked frames through ``_import_chunk``,
4. returns per-row statuses and summary counters.

Configuration validation
^^^^^^^^^^^^^^^^^^^^^^^^

``ConfigValidator.validate()`` enforces:

- required top-level keys: ``file_format``, ``order``, ``models``,
- file format in ``csv/xlsx/xls``,
- each ordered step exists in ``models``,
- each step has at least one field mapping group,
- structure of ``transformed_columns``, ``lookup_fields``, ``computed_fields``,
- ``required_fields`` must reference declared field mappings,
- ``reference_fields`` must point to prior steps (not later steps),
- every referenced transform/generator must exist in provided transform dict.

This validation happens in service constructor, not lazily on import execution.

File reading constraints
^^^^^^^^^^^^^^^^^^^^^^^^

``FileReader``:

- CSV uses ``pandas.read_csv`` with optional delimiter/encoding,
- XLSX uses ``read_excel(..., engine="openpyxl", header=4)``,
- XLS uses ``read_excel(..., engine="xlrd", header=4)``,
- headers are stripped for whitespace,
- header validation is strict: extra or missing columns raise ``ImportValidationError``.

Design consequence:

Input templates are effectively schema-locked. Operationally this reduces ambiguity but increases template coupling.

Row processing internals
^^^^^^^^^^^^^^^^^^^^^^^^

For each chunk, service does:

- initialize row results with ``status=pending`` and row number,
- pre-collect lookup values and prefetch lookup objects,
- process model steps in configured order,
- per row per step build ``kwargs`` via ``DataProcessor.prepare_kwargs_for_row``,
- decide create/update based on ``unique_by`` + ``update_if_exists``,
- persist created/updated objects,
- aggregate summary counts.

Field processing order (important)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``prepare_kwargs_for_row`` executes in this exact order:

1. computed fields,
2. direct columns,
3. transformed columns,
4. constant fields,
5. reference fields,
6. lookup fields,
7. required-field validation.

Why it matters:

- computed values can be overwritten by later direct/transformed mappings targeting same model field.
- required-field validation happens after all transformation and lookup resolution.

Lookup strategy
^^^^^^^^^^^^^^^

``LookupManager`` prefetches lookup targets to avoid per-row lookup queries.

- lookup cache key format: ``<app_label.ModelName>__<lookup_field>``,
- lookup fields must be database fields on the lookup model,
- prefetch uses ORM ``field__in`` query only.

Validation behavior:

- configuration validation fails when a lookup field is not a concrete model field.

Unique detection and updates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``ObjectManager.prefetch_existing_objects`` builds a map keyed by tuple of ``unique_by`` values.

- values can come from direct/transformed/constant/computed mappings,
- transformed and computed values are evaluated during prefetch,
- rows with missing unique values are skipped from existing-object map.
- after prefetch, the step keeps this key map live during row iteration by registering newly staged create instances,
- repeated ``unique_by`` keys in the same chunk resolve to the staged instance instead of creating duplicates,
- with ``update_if_exists=False``, any row that matches an existing/staged ``unique_by`` key is marked failed.

Persistence strategy
^^^^^^^^^^^^^^^^^^^^

For each step:

- objects to create are accumulated,
- objects to update are accumulated,
- update fields are unioned.

Step dependency handling:

- if current step is referenced by later steps, create path is forced to individual ``save()`` to guarantee PK availability in ``created_objs``.
- otherwise bulk create path is attempted.

Bulk operation fallback behavior
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``BulkOperations``:

- bulk create attempts batch create and falls back to per-instance saves on exception,
- bulk update attempts one ``bulk_update`` and falls back to individual ``save(update_fields=...)``,
- fallback save errors are returned with row indices so caller can mark row-level failures in response payload.

Savepoint handling:

- bulk create executes inside a nested ``transaction.atomic()`` savepoint boundary,
- successful bulk batches release the savepoint,
- bulk errors roll back to the savepoint before per-row fallback is attempted.

Row status semantics
^^^^^^^^^^^^^^^^^^^^

Row processing status is deterministic across multi-step imports:

- once a row is marked ``failed``, later steps do not overwrite it,
- later model steps skip rows already marked ``failed``,
- create/update persistence failures are attached to row errors and row status is set to ``failed``,
- summary counters are derived from final per-row status.

Chunking behavior
^^^^^^^^^^^^^^^^^

When ``chunk_size < len(df)``:

- chunks are processed independently,
- chunk-level exception marks all rows in chunk failed with same error,
- summary totals are aggregated across chunks.

This improves survivability for very large files but does not provide exactly-once semantics across chunks.

When not to use current import service
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- when template columns cannot be rigidly enforced,
- when row-level deterministic idempotency is mandatory without custom reconciliation.

Alternatives
^^^^^^^^^^^^

- API-first ingestion with per-row serializer validation and queue-backed processing,
- ETL pipeline tools for high-volume imports,
- custom upsert SQL for single-model high-throughput data feeds.


Management Command: ``generate_import_template``
------------------------------------------------

Purpose
^^^^^^^

Generate import template files directly from a viewset's ``import_file_config``.

Behavior highlights
^^^^^^^^^^^^^^^^^^^

- resolves viewset class via multiple module path heuristics,
- validates presence/shape of ``import_file_config``,
- extracts columns from direct/transformed/lookup and computed (``if_empty``) fields,
- infers optional/required columns from ``required_fields`` and computed rules,
- supports ordering modes: ``config``, ``required-first``, ``alphabetic``,
- writes XLSX with legend and color coding (red required, green optional),
- can emit CSV template.

Operational limits
^^^^^^^^^^^^^^^^^^

- relies on dynamic import heuristics; non-standard project layouts may require explicit module paths,
- template path is ``<BASE_DIR>/static/import-templates``.


Compatibility and Dependency Matrix
-----------------------------------

Core service compatibility:

- Django >= 3.2
- DRF >= 3.12

Optional dependencies:

- export to xlsx: ``openpyxl``
- export to pdf: ``weasyprint``
- import: ``pandas`` (+ openpyxl/xlrd for excel engines)
- docs header integration: ``django-constance`` optional (graceful fallback if unavailable)


Integration Patterns
--------------------

Pattern 1: synchronous administrative import/export
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- expose import/export actions only to privileged staff,
- keep strict template contract,
- enable detailed error payloads for operator remediation.

Pattern 2: async orchestration wrapper
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- keep service logic but move invocation to background jobs,
- persist result payloads in job records,
- expose polling endpoints for import/export job status.

Pattern 3: staged migration from legacy import
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. model legacy CSV to ``import_file_config`` in shadow mode.
2. run service against copied files and compare DB outcomes.
3. switch production endpoint to new service.
4. keep old importer as fallback during burn-in period.


Performance Summary
-------------------

Export:

- CPU bound by serialization/formatting, memory bound by full in-memory dataset.

Import:

- CPU bound by pandas parsing and transform functions,
- DB bound by lookup prefetch queries + create/update writes,
- chunking controls memory but not total query complexity.

Main scaling levers:

- ``COMMON_IMPORT_BATCH_SIZE``,
- per-import ``chunk_size`` in config,
- reducing expensive transform/generator logic,
- ensuring lookup fields map to indexed DB columns where possible.

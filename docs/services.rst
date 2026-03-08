Services
========

drf-commons includes two production-ready service classes for file-based data
operations: file export and file import.

File Export Service
-------------------

ExportService
~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.services.export_file import ExportService

Generates file exports in CSV, XLSX, and PDF formats from structured data.

**Supported formats**:

.. list-table::
   :widths: 15 30 55
   :header-rows: 1

   * - Format
     - Requirement
     - Notes
   * - ``csv``
     - Core (no extras)
     - UTF-8 encoded, suitable for data exchange
   * - ``xlsx``
     - ``drf-commons[export]``
     - Full Excel workbook with configurable column widths and headers
   * - ``pdf``
     - ``drf-commons[export]``
     - Formatted table via weasyprint; suitable for human-readable reports

**Direct usage**:

.. code-block:: python

   from drf_commons.services.export_file import ExportService

   service = ExportService()
   data = ArticleSerializer(queryset, many=True).data

   # CSV
   response = service.export_csv(data, field_config={"title": "Title", "published": "Published"})

   # XLSX
   response = service.export_xlsx(
       data,
       field_config={"title": "Title", "created_at": "Date"},
       column_config={"title": {"width": 40}},
   )

   # PDF
   response = service.export_pdf(data, field_config={"title": "Title"})

**Via FileExportMixin** (recommended):

.. code-block:: python

   class ArticleViewSet(BaseViewSet):
       export_field_config = {
           "title": "Article Title",
           "published": "Status",
           "created_at": "Date Created",
           "created_by__username": "Author",
       }

   # POST /articles/export/
   {
     "file_type": "xlsx",
     "includes": ["title", "published", "created_at"],
     "column_config": {
       "title": {"width": 50, "header": "Article Title"}
     }
   }

The exported file is returned as an ``HttpResponse`` with appropriate
``Content-Disposition`` and MIME type headers.

File Import Service
-------------------

FileImportService
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.services.import_from_file import FileImportService

Processes file imports from CSV, XLS, and XLSX formats. Supports multi-model
imports with dependency ordering, foreign key resolution, data transformation
hooks, and progress callbacks.

Import Configuration Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``import_file_config`` dict (set on the ViewSet or passed directly to the
service) defines the complete import specification:

.. code-block:: python

   import_file_config = {
       # Required: file format
       "file_format": "xlsx",              # "csv", "xls", "xlsx"

       # Required: processing order for models (dependency-first)
       "order": ["country", "city", "person"],

       # Required: model definitions
       "models": {
           "country": {
               "model": Country,           # Django model class
               "fields": ["name", "code"], # Columns to import
               "unique_fields": ["code"],  # Fields for upsert lookup
           },
           "city": {
               "model": City,
               "fields": ["name", "country_code"],
               "unique_fields": ["name", "country_code"],
               "foreign_keys": {
                   # Map a column to a related model
                   "country": {
                       "model": Country,
                       "lookup_field": "code",
                       "source_field": "country_code",
                   }
               },
           },
           "person": {
               "model": Person,
               "fields": ["first_name", "last_name", "email", "city_name"],
               "unique_fields": ["email"],
               "foreign_keys": {
                   "city": {
                       "model": City,
                       "lookup_field": "name",
                       "source_field": "city_name",
                   }
               },
           },
       },

       # Optional: process large files in chunks
       "chunk_size": 500,
   }

Transformation Hooks
~~~~~~~~~~~~~~~~~~~~

The ``import_transforms`` dict on the ViewSet applies per-field transformations
before data is written to the database:

.. code-block:: python

   class PersonViewSet(ImportableViewSet):
       import_file_config = { ... }

       import_transforms = {
           "email": lambda v: v.strip().lower(),
           "first_name": lambda v: v.strip().title(),
           "last_name": lambda v: v.strip().title(),
           "phone": lambda v: re.sub(r"\D", "", v),  # digits only
       }

Progress Callbacks
~~~~~~~~~~~~~~~~~~

For long-running imports, pass a progress callback to the service:

.. code-block:: python

   def on_progress(processed: int, total: int, errors: list):
       logger.info(f"Import progress: {processed}/{total} rows ({len(errors)} errors)")

   service = FileImportService(
       config=import_file_config,
       transforms=import_transforms,
   )
   result = service.import_file(
       file_obj=uploaded_file,
       progress_callback=on_progress,
   )

Import Result
~~~~~~~~~~~~~

The service returns a structured result dict:

.. code-block:: python

   {
       "success": True,
       "processed": 1200,
       "failed": 3,
       "errors": [
           {"row": 45, "field": "email", "message": "Email already exists"},
           {"row": 89, "field": "country_code", "message": "Country 'XX' not found"},
       ],
       "created": 800,
       "updated": 397,
   }

Import Template Generation
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``generate_import_template`` management command generates a sample import
file based on the ViewSet's ``import_file_config``:

.. code-block:: bash

   python manage.py generate_import_template PersonViewSet

This generates a file (XLSX by default) with:

* One sheet per model in the import config
* Column headers matching the ``fields`` list
* Example data in the first data row

Chunk-Based Processing
~~~~~~~~~~~~~~~~~~~~~~

For very large files, set ``chunk_size`` in the import config. The service
reads the file in chunks and processes each chunk in its own transaction:

.. code-block:: python

   import_file_config = {
       "file_format": "xlsx",
       "chunk_size": 250,          # Process 250 rows per transaction
       "order": ["person"],
       "models": { ... },
   }

This bounds peak memory usage and ensures that a failure in one chunk does not
roll back the entire import.

DataProcessor
~~~~~~~~~~~~~

The import pipeline internal components:

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Component
     - Responsibility
   * - ``FileReader``
     - Reads CSV/XLS/XLSX into a pandas DataFrame
   * - ``ConfigValidator``
     - Validates the ``import_file_config`` at service construction
   * - ``DataProcessor``
     - Applies transforms, resolves foreign keys, validates rows
   * - ``BulkOperations``
     - Executes ``bulk_create()`` / ``bulk_update()`` for each model chunk

These components are internal to the service and are not part of the public
API. Customize import behavior through the configuration interface, transforms,
and progress callbacks.

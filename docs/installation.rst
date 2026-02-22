Installation
============

Requirements
------------

drf-commons requires:

* Python 3.8 or higher
* Django 3.2 or higher
* Django REST Framework 3.12 or higher

Core Installation
-----------------

Install the base package from PyPI:

.. code-block:: bash

   pip install drf-commons

The core installation includes the full view layer, model mixins, serializer
utilities, response formatting, middleware, pagination, and filtering. It does
**not** install optional feature dependencies.

Optional Feature Sets
---------------------

drf-commons uses extras to keep the core dependency surface minimal:

.. code-block:: bash

   # File export support (CSV, XLSX, PDF)
   pip install drf-commons[export]

   # File import support (CSV, XLS, XLSX via pandas)
   pip install drf-commons[import]

   # Debug and profiling utilities (psutil)
   pip install drf-commons[debug]

   # All optional features
   pip install drf-commons[export,import,debug]

.. list-table:: Optional Dependencies
   :widths: 15 35 50
   :header-rows: 1

   * - Extra
     - Packages Installed
     - Enables
   * - ``export``
     - ``openpyxl>=3.0``, ``weasyprint>=60.0``
     - :class:`~drf_commons.services.export_file.service.ExportService` (XLSX, PDF)
   * - ``import``
     - ``openpyxl>=3.0``, ``pandas>=1.3``
     - :class:`~drf_commons.services.import_from_file.service.FileImportService`
   * - ``debug``
     - ``psutil>=5.9``
     - Memory usage monitoring in debug utilities

Development Installation
------------------------

For contributing or local development:

.. code-block:: bash

   git clone https://github.com/htvictoire/drf-commons
   cd drf-commons

   # Full development environment
   pip install -e ".[export,import,debug]"

   # Install development tools
   pip install -e ".[dev,test]"

   # Install documentation tools
   pip install -r docs/requirements.txt

Django Application Setup
------------------------

Add ``drf_commons`` to your ``INSTALLED_APPS``:

.. code-block:: python

   # settings.py
   INSTALLED_APPS = [
       "django.contrib.contenttypes",
       "django.contrib.auth",
       ...
       "rest_framework",
       "drf_commons",
       ...
   ]

Middleware Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

If you use :class:`~drf_commons.models.base.UserActionMixin` or
:class:`~drf_commons.models.fields.CurrentUserField`, add
:class:`~drf_commons.middlewares.current_user.CurrentUserMiddleware` to your
middleware stack:

.. code-block:: python

   MIDDLEWARE = [
       "django.middleware.security.SecurityMiddleware",
       ...
       "drf_commons.middlewares.CurrentUserMiddleware",
       ...
   ]

.. important::

   ``CurrentUserMiddleware`` must be placed after Django's authentication
   middleware (``django.contrib.auth.middleware.AuthenticationMiddleware``)
   to ensure ``request.user`` is populated when the middleware executes.

Configuration Namespace
-----------------------

drf-commons reads its configuration from the ``COMMON`` dictionary in
``settings.py``. All settings have defaults and are optional:

.. code-block:: python

   COMMON = {
       # Batch sizing
       "BULK_OPERATION_BATCH_SIZE": 1000,
       "IMPORT_BATCH_SIZE": 250,

       # Performance thresholds (seconds)
       "DEBUG_SLOW_REQUEST_THRESHOLD": 1.0,
       "DEBUG_SLOW_QUERY_THRESHOLD": 0.1,

       # Query thresholds (count)
       "DEBUG_HIGH_QUERY_COUNT_THRESHOLD": 10,

       # Failed row display limit in import reports
       "IMPORT_FAILED_ROWS_DISPLAY_LIMIT": 10,
   }

Verifying Installation
----------------------

.. code-block:: python

   import drf_commons
   print(drf_commons.__version__)

   from drf_commons.models import BaseModelMixin
   from drf_commons.views import BaseViewSet
   from drf_commons.serializers import BaseModelSerializer
   from drf_commons.response import success_response, error_response

All imports at the top level are the primary public API.

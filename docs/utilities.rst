Utilities
=========

drf-commons includes utility modules for debug instrumentation, structured
logging, and middleware validation.

Debug Package
-------------

The ``debug`` package provides structured logging and development observability
tools.

StructuredLogger
~~~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.debug import StructuredLogger

A category-based logger for structured, machine-readable log output. Provides
purpose-specific log methods for common API observability concerns.

.. code-block:: python

   logger = StructuredLogger("myapp")

**Methods**:

log_user_action
^^^^^^^^^^^^^^^

.. code-block:: python

   logger.log_user_action(
       user,           # AbstractBaseUser
       action: str,    # "CREATE", "UPDATE", "DELETE", etc.
       resource: str,  # Model name or resource identifier
       details: dict,  # Arbitrary context
   )

Use for audit trail logging at the service or view layer.

.. code-block:: python

   logger.log_user_action(
       user=request.user,
       action="BULK_DELETE",
       resource="Article",
       details={"count": 15, "ids": deleted_ids},
   )

log_api_request
^^^^^^^^^^^^^^^

.. code-block:: python

   logger.log_api_request(
       request,        # DRF or Django request
       response,       # DRF or Django response
       duration: float,  # Seconds
   )

log_error
^^^^^^^^^

.. code-block:: python

   logger.log_error(
       error: Exception,
       context: dict = None,
   )

log_performance
^^^^^^^^^^^^^^^

.. code-block:: python

   logger.log_performance(
       operation: str,
       duration: float,    # Seconds
       details: dict = None,
   )

Logging Categories
~~~~~~~~~~~~~~~~~~

The debug package organizes logging by category. Categories are defined in
``drf_commons.debug.core.categories`` and can be selectively enabled in
the ``COMMON`` settings:

.. code-block:: python

   COMMON = {
       "DEBUG_ENABLED_CATEGORIES": ["API", "DATABASE", "PERFORMANCE"],
   }

Available categories: ``API``, ``DATABASE``, ``CACHE``, ``PERFORMANCE``,
``ERRORS``, ``USER_ACTIONS``.

Debug Utilities
~~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.debug.utils import (
       debug_print,
       debug_sql_queries,
       capture_request_data,
       log_model_changes,
       profile_function,
       memory_usage,
   )

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Function
     - Description
   * - ``debug_print(obj)``
     - Pretty-prints any object with type information
   * - ``debug_sql_queries(queries)``
     - Formats and prints SQL queries from Django's query log
   * - ``capture_request_data(request)``
     - Returns a dict with request method, path, headers, and body
   * - ``log_model_changes(old, new)``
     - Diffs two model instances and logs changed fields
   * - ``profile_function(fn, *args)``
     - Runs ``fn(*args)`` under cProfile and logs results
   * - ``memory_usage()``
     - Returns current process memory in MB (requires ``psutil``)

Middleware Checker
------------------

.. code-block:: python

   from drf_commons.utils.middleware_checker import MiddlewareChecker, require_middleware

MiddlewareChecker
~~~~~~~~~~~~~~~~~

Provides runtime middleware validation.

.. code-block:: python

   checker = MiddlewareChecker()

   # Check if a middleware is installed
   is_installed = checker.is_installed("drf_commons.middlewares.CurrentUserMiddleware")

   # Require a middleware or raise ImproperlyConfigured
   checker.require("drf_commons.middlewares.CurrentUserMiddleware")

require_middleware
~~~~~~~~~~~~~~~~~

A decorator that enforces middleware presence before a function executes:

.. code-block:: python

   from drf_commons.utils.middleware_checker import require_middleware

   @require_middleware("drf_commons.middlewares.CurrentUserMiddleware")
   def my_service_function():
       user = get_current_user()
       ...

enforce_current_user_middleware_if_used
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Called automatically from ``DrfCommonsConfig.ready()``. Inspects the
installed application models and enforces ``CurrentUserMiddleware`` if any
model uses ``UserActionMixin`` or ``CurrentUserField``.

This function should not be called manually in application code.

Template Tags
-------------

.. code-block:: python

   {% load dict_extras %}

The ``dict_extras`` template tag library provides utility filters for working
with dictionary objects in Django templates. Included primarily to support
admin template customizations in projects using drf-commons model data in
Django templates.

Test Utilities
--------------

See :doc:`testing` for the complete testing utilities documentation.

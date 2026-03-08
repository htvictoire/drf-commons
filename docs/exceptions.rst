Exceptions
==========

drf-commons defines a small set of domain-specific exceptions and integrates
with DRF's exception handling framework.

Package Exceptions
------------------

VersionConflictError
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from drf_commons.models.content import VersionConflictError

Raised by :class:`~drf_commons.models.content.VersionMixin` when a concurrent
write is detected. Extends ``Exception``.

The version conflict is detected in ``save()`` using a conditional update:

.. code-block:: python

   # Simplified internal implementation
   updated = MyModel.objects.filter(
       pk=self.pk,
       version=self.version - 1,  # expected previous version
   ).update(version=self.version)

   if not updated:
       raise VersionConflictError(
           f"Version conflict on {self.__class__.__name__} pk={self.pk}. "
           f"Expected version {self.version - 1}, record has been modified."
       )

**Handling in a ViewSet**:

.. code-block:: python

   from drf_commons.models.content import VersionConflictError
   from drf_commons.response import error_response
   from drf_commons.views import BaseViewSet

   class DocumentViewSet(BaseViewSet):
       def perform_update(self, serializer):
           try:
               serializer.save()
           except VersionConflictError as exc:
               return error_response(
                   message="This document has been modified by another user. "
                           "Please refresh and retry.",
                   status_code=409,
               )

ImportError Exceptions
~~~~~~~~~~~~~~~~~~~~~~~

File import operations can raise structured exceptions from
``drf_commons.services.import_from_file.core.exceptions``:

* ``ImportConfigurationError`` — Invalid import configuration
* ``FileFormatError`` — Unsupported or malformed file
* ``ImportValidationError`` — Row-level validation failure with row details
* ``ImportOperationError`` — Database-level failure during import

These are raised by :class:`~drf_commons.services.import_from_file.service.FileImportService`
and should be caught in the viewset or caught globally.

DRF Exception Integration
--------------------------

drf-commons ViewSets allow DRF's standard ``APIException`` subclasses to flow
through normally. The response envelope is applied at the mixin level, not at
the exception handler level.

For custom exception handling, use DRF's ``EXCEPTION_HANDLER`` setting:

.. code-block:: python

   # settings.py
   REST_FRAMEWORK = {
       "EXCEPTION_HANDLER": "myapp.exceptions.custom_exception_handler",
   }

   # myapp/exceptions.py
   from rest_framework.views import exception_handler
   from drf_commons.response import error_response

   def custom_exception_handler(exc, context):
       response = exception_handler(exc, context)

       if response is not None:
           return error_response(
               message=str(exc.detail) if hasattr(exc, "detail") else str(exc),
               errors=response.data if isinstance(response.data, dict) else None,
               status_code=response.status_code,
           )

       return response

ImproperlyConfigured Errors
---------------------------

drf-commons raises Django's ``ImproperlyConfigured`` at application startup
in the following cases:

**Missing CurrentUserMiddleware**:

Occurs when any installed model uses ``UserActionMixin`` or ``CurrentUserField``
but ``CurrentUserMiddleware`` is not in the ``MIDDLEWARE`` setting.

.. code-block:: text

   django.core.exceptions.ImproperlyConfigured:
   drf_commons.middlewares.CurrentUserMiddleware is required because model
   'myapp.Article' uses UserActionMixin. Add it to MIDDLEWARE.

**Missing optional dependency**:

Occurs when an export/import feature is used without installing the required
extra:

.. code-block:: text

   django.core.exceptions.ImproperlyConfigured:
   Install drf-commons[export] to use XLSX export (openpyxl required).

These startup-time errors are intentional. They surface configuration problems
as early as possible — at process start — rather than at the first API request
that exercises the misconfigured code path.

Responses
=========

drf-commons enforces a standardized JSON response envelope across all API
endpoints. This eliminates the need for client-side conditional parsing based
on response structure.

Response Envelope Structure
---------------------------

All responses conform to the following schema:

**Success**:

.. code-block:: json

   {
     "success": true,
     "timestamp": "2024-01-15T10:30:00.000000Z",
     "message": "Operation completed successfully.",
     "data": { ... }
   }

**Error**:

.. code-block:: json

   {
     "success": false,
     "timestamp": "2024-01-15T10:30:00.000000Z",
     "message": "Validation failed.",
     "errors": {
       "title": ["This field is required."],
       "email": ["Enter a valid email address."]
     },
     "data": null
   }

.. list-table:: Envelope Fields
   :widths: 15 10 75
   :header-rows: 1

   * - Field
     - Type
     - Description
   * - ``success``
     - ``bool``
     - ``true`` on 2xx responses, ``false`` on error responses
   * - ``timestamp``
     - ``str``
     - ISO 8601 UTC timestamp of response generation
   * - ``message``
     - ``str``
     - Human-readable description; may be empty on success
   * - ``data``
     - ``any``
     - Response payload; ``null`` on error
   * - ``errors``
     - ``object``
     - Field-level or non-field errors; present only on error responses

The ``timestamp`` field uses Django's ``DjangoJSONEncoder``, ensuring UTC
output in ISO 8601 format regardless of the server's local timezone
configuration.

Response Utility Functions
--------------------------

.. code-block:: python

   from drf_commons.response import success_response, error_response

success_response
~~~~~~~~~~~~~~~~

.. code-block:: python

   success_response(
       data=None,
       message: str = "",
       status_code: int = 200,
       **kwargs,
   ) -> Response

Constructs a DRF ``Response`` with the success envelope.

**Parameters**:

* ``data`` — The response payload. Passed through ``DjangoJSONEncoder``
  serialization. Can be any JSON-serializable value.
* ``message`` — Optional human-readable success message.
* ``status_code`` — HTTP status code. Defaults to ``200``.
* ``**kwargs`` — Additional fields merged into the response envelope.

**Examples**:

.. code-block:: python

   # Simple success
   return success_response(data=serializer.data)

   # With message and non-200 status
   return success_response(
       data={"created": 15},
       message="Bulk create completed.",
       status_code=201,
   )

   # With additional envelope fields
   return success_response(
       data=serializer.data,
       meta={"total_pages": 10, "current_page": 1},
   )

error_response
~~~~~~~~~~~~~~

.. code-block:: python

   error_response(
       message: str = "An error occurred.",
       status_code: int = 400,
       errors=None,
       **kwargs,
   ) -> Response

Constructs a DRF ``Response`` with the error envelope.

**Parameters**:

* ``message`` — Human-readable error description.
* ``status_code`` — HTTP status code. Defaults to ``400``.
* ``errors`` — Dict of field-level or non-field errors.
* ``**kwargs`` — Additional fields merged into the response envelope.

**Examples**:

.. code-block:: python

   # Validation error
   return error_response(
       message="Validation failed.",
       errors=serializer.errors,
       status_code=400,
   )

   # Not found
   return error_response(
       message="Article not found.",
       status_code=404,
   )

   # Permission denied
   return error_response(
       message="You do not have permission to perform this action.",
       status_code=403,
   )

Automatic Response Formatting
-------------------------------

When using drf-commons ViewSets, response formatting is automatic. The CRUD
and bulk action mixins call ``success_response()`` and ``error_response()``
internally. No per-view code is required for standard operations.

Custom views and actions can use the utilities directly:

.. code-block:: python

   from rest_framework.decorators import action
   from drf_commons.response import success_response, error_response
   from drf_commons.views import BaseViewSet

   class ReportViewSet(BaseViewSet):
       @action(detail=False, methods=["post"], url_path="generate")
       def generate_report(self, request):
           try:
               result = ReportService.generate(request.data)
               return success_response(
                   data=result,
                   message="Report generated successfully.",
               )
           except ValueError as exc:
               return error_response(
                   message=str(exc),
                   status_code=422,
               )

Pagination Response Format
--------------------------

Paginated list responses include standard pagination metadata alongside
the ``data`` array:

.. code-block:: json

   {
     "success": true,
     "timestamp": "2024-01-15T10:30:00.000000Z",
     "message": "",
     "count": 150,
     "next": "https://api.example.com/articles/?page=3",
     "previous": "https://api.example.com/articles/?page=1",
     "data": [ ... ]
   }

For unpaginated list responses (``?paginated=false`` or when
``pagination_class = None``), the ``count``, ``next``, and ``previous`` fields
are absent and ``data`` contains the full array.

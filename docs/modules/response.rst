response
========

Source module: ``drf_commons/response/utils.py``

Why this module exists
----------------------

Problem
^^^^^^^

DRF responses are flexible; teams often drift into inconsistent payload envelopes across endpoints.

Default DRF behavior
^^^^^^^^^^^^^^^^^^^^

- serializer output is returned directly unless wrapped manually,
- error shape varies by exception type and handler configuration.

What ``drf-commons`` provides
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Three helper constructors:

- ``success_response``
- ``error_response``
- ``validation_error_response``

All include timestamped envelope fields.

``success_response`` behavior
-----------------------------

- always sets ``success=True`` and ``timestamp`` (ISO datetime),
- optional ``message``,
- optional ``data`` (dict/list/primitive; stored under ``data`` key),
- optional ``headers`` passed to DRF ``Response``,
- merges additional keyword args into root payload.

Use case fit
^^^^^^^^^^^^

- consistent API contract for client teams,
- easy inclusion of endpoint-specific metadata without custom response classes.

``error_response`` behavior
---------------------------

- always sets ``success=False``, ``timestamp``, ``message``,
- optional ``errors`` object,
- additional ``kwargs`` merged at root,
- default status code 400 unless overridden.

``validation_error_response`` behavior
--------------------------------------

- delegates to ``error_response`` with status code 422,
- intended for semantic validation failures distinct from malformed request syntax.

Performance implications
------------------------

Negligible overhead: envelope construction is small dictionary assembly.

Trade-offs
----------

Pros:

- stable client-facing envelope,
- lower drift across endpoints.

Cons:

- diverges from DRF default exception payload conventions,
- can conflict with teams expecting RFC7807/problem+json style errors.

When not to use
---------------

- APIs intentionally exposing raw DRF serializer/error shapes,
- systems standardized on external API error contracts incompatible with this envelope.

Alternatives
------------

- custom global exception handler plus DRF native responses,
- standardized problem detail implementation.

Integration pattern
-------------------

.. code-block:: python

   from rest_framework import status
   from drf_commons.response.utils import success_response, error_response

   def finalize_job(request, job_id):
       job = get_job(job_id)
       if job.is_locked:
           return error_response(
               message="Job is locked",
               status_code=status.HTTP_409_CONFLICT,
               errors={"job_id": ["Cannot finalize locked job"]},
           )

       job.finalize()
       return success_response(
           message="Job finalized",
           status_code=status.HTTP_200_OK,
           data={"job_id": str(job.id), "state": job.state},
       )

Migration strategy
------------------

1. introduce envelope on new API versions,
2. maintain compatibility adapters for old clients,
3. migrate exception handling to map legacy errors into unified envelope.

Compatibility concerns
----------------------

Because helpers are lightweight, they compose with DRF pagination/serialization/permissions without additional framework hooks.

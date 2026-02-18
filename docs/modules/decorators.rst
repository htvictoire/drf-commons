decorators
==========

Source modules:

- ``drf_commons/decorators/cache.py``
- ``drf_commons/decorators/database.py``
- ``drf_commons/decorators/logging.py``
- ``drf_commons/decorators/performance.py``

Purpose
-------

These decorators provide instrumentation wrappers, not business logic wrappers.

Problem they solve
^^^^^^^^^^^^^^^^^^

In DRF services, teams need lightweight, reusable observability hooks without copying timing/logging code into each function.

How DRF normally behaves
^^^^^^^^^^^^^^^^^^^^^^^^^

DRF offers request lifecycle hooks and logging integration, but no fine-grained function decorators for cache/db/performance categories.

Category-aware logging model
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All decorators obtain loggers through ``Categories.get_logger(...)``. Disabled categories return ``NullLogger`` so calls become no-op.

``cache_debug``
---------------

Behavior
^^^^^^^^

- computes cache key via custom callable or fallback hash of args/kwargs,
- logs start and completion timing around wrapped call.

Limitations
^^^^^^^^^^^

- does not interact with Django cache backend directly,
- fallback key generation uses Python ``hash`` over stringified args, which is process-specific and not stable across runs.

When not to use
^^^^^^^^^^^^^^^

Do not treat it as cache implementation or cache key canonicalization strategy.

``log_db_query``
----------------

Behavior
^^^^^^^^

- snapshots ``len(connection.queries)`` before call,
- after call logs delta query count and elapsed time,
- logs individual SQL statements from new query slice,
- logs and re-raises exceptions.

Performance and risk
^^^^^^^^^^^^^^^^^^^^

- can generate large logs in query-heavy code paths,
- depends on Django query logging being active for meaningful output,
- SQL text may contain sensitive details; category configuration and retention policy matter.

``api_request_logger``
----------------------

Behavior
^^^^^^^^

- logs method/path and status,
- optional headers/body logging,
- always logs query params.

Edge cases
^^^^^^^^^^

- body decoding failures are treated as binary data and logged accordingly,
- assumes wrapped callable signature starts with ``request``.

``log_function_call``
---------------------

Behavior
^^^^^^^^

- logs entry (with optional args/kwargs),
- times execution,
- logs completion and optional result,
- logs and re-raises exceptions.

Trade-off
^^^^^^^^^

Useful for targeted diagnostics; avoid on high-frequency hot paths with large argument/result payloads.

``log_exceptions``
------------------

Behavior
^^^^^^^^

- catches and logs exception details with traceback and extra metadata,
- configurable re-raise behavior.

When not to use
^^^^^^^^^^^^^^^

Avoid ``reraise=False`` in core business paths unless explicit exception suppression is intended and tested.

``api_performance_monitor``
---------------------------

Behavior
^^^^^^^^

- times wrapped request handler,
- logs warning if duration exceeds threshold,
- logs error and re-raises on exception.

Production use
^^^^^^^^^^^^^^

Good for lightweight endpoint timing before introducing full tracing stack.

Real integration example
------------------------

.. code-block:: python

   from drf_commons.decorators.performance import api_performance_monitor
   from drf_commons.decorators.logging import api_request_logger
   from drf_commons.decorators.database import log_db_query

   @api_request_logger(log_body=False, log_headers=False)
   @api_performance_monitor(threshold=0.75)
   @log_db_query(query_type="invoice-finalize")
   def finalize_invoice(request, invoice_id):
       invoice = Invoice.objects.select_related("customer").get(pk=invoice_id)
       invoice.finalize()
       return Response({"id": str(invoice.id), "state": invoice.state})

Compatibility concerns
----------------------

- works with Django/DRF logging stack,
- behavior quality depends on ``debug`` category configuration.

Alternative approaches
----------------------

- OpenTelemetry decorators/middleware,
- APM instrumentation libraries,
- explicit structured logs in service layer.

Migration strategy
------------------

1. start with performance and exception logging on high-value endpoints,
2. monitor log volume and sensitivity,
3. expand category coverage selectively.

debug
=====

Source modules:

- ``drf_commons/debug/core/categories.py``
- ``drf_commons/debug/logger.py``
- ``drf_commons/debug/utils.py``
- ``drf_commons/debug/logging/*``

Why this subsystem exists
-------------------------

Problem
^^^^^^^

Most DRF projects either:

- over-log everything (high noise, high cost), or
- under-log critical paths (poor debuggability).

Default DRF behavior
^^^^^^^^^^^^^^^^^^^^

DRF integrates with Django logging but does not provide category-level feature toggling or a no-op logger strategy.

Core design
-----------

Category gating with ``NullLogger``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``Categories.get_logger(name, category)`` returns:

- real logger if category enabled,
- singleton ``NullLogger`` if disabled.

Enablement rules:

- category must be in ``DEBUG_ENABLED_LOG_CATEGORIES``,
- when ``DEBUG=False``, category must also be in ``DEBUG_PRODUCTION_SAFE_CATEGORIES``.

This means instrumentation calls can remain in production code without defensive ``if`` checks.

StructuredLogger
^^^^^^^^^^^^^^^^

``StructuredLogger`` provides standardized log methods for:

- user actions,
- API requests,
- errors,
- performance metrics.

It resolves username using configured user model's ``USERNAME_FIELD``.

Debug utilities
---------------

Notable utilities and behavior:

- ``debug_print``: prints only when category active,
- ``pretty_print_dict``: readable object/dict inspection with configured formatting,
- ``debug_sql_queries``: prints executed SQL and optional reset,
- ``capture_request_data``: request snapshot with sensitive header filtering,
- ``log_model_changes``: logs model change details and optional field diffs,
- ``profile_function``: cProfile wrapper returning result + stats text,
- ``memory_usage``: process/system memory snapshot via ``psutil``,
- ``analyze_queryset``: SQL/count/sample logging,
- ``debug_context_processor``: template debug context when enabled.

Dependency contract:

- ``memory_usage`` loads ``psutil`` when invoked,
- install requirement: ``pip install drf-commons[debug]``.

Performance implications
^^^^^^^^^^^^^^^^^^^^^^^^

- when categories are disabled, overhead is minimal due to null logger pattern,
- when enabled heavily, logging I/O can dominate runtime in hot paths,
- profiling and SQL dump utilities are diagnostic tools and should be used selectively.

Logging configuration builder
-----------------------------

``build_logging_config(base_dir, debug_mode=False)`` composes:

- formatter config,
- handler config filtered by enabled categories,
- logger config filtered by enabled categories,
- root handlers from available system handlers.

It also ensures required log directories exist.

Trade-offs
----------

Pros:

- centralized observability controls,
- production-safe category filtering,
- clean call sites without category-check noise.

Cons:

- category misconfiguration can silently disable expected logs,
- file-based logging requires correct filesystem permissions and rotation strategy.

When not to use
---------------

- teams already fully standardized on external tracing/APM and do not want parallel logging conventions.

Alternatives
------------

- OpenTelemetry logging/tracing stack,
- direct integration with vendor APM SDKs,
- strict structured event pipelines (for example JSON logs to centralized collector only).

Integration example
-------------------

.. code-block:: python

   from pathlib import Path
   from drf_commons.debug.logging.config import build_logging_config

   LOGGING = build_logging_config(
       base_dir=Path(BASE_DIR),
       debug_mode=DEBUG,
   )

   COMMON_DEBUG_ENABLED_LOG_CATEGORIES = [
       "errors",
       "database",
       "performance",
       "requests",
   ]

Migration strategy
------------------

1. enable only ``errors`` category first,
2. add ``database`` and ``performance`` in staging,
3. tune thresholds and rotation sizes,
4. enable additional categories based on operational value.

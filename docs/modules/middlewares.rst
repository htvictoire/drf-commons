middlewares
===========

Source modules:

- ``drf_commons/middlewares/current_user.py``
- ``drf_commons/middlewares/debug.py``

Why middleware exists in this library
-------------------------------------

Two DRF-adjacent production concerns are handled here:

- request-scoped actor propagation into lower layers,
- request/SQL/profiling observability with category-aware logging.

Current User Middleware
-----------------------

Problem it solves
^^^^^^^^^^^^^^^^^

Model utilities needing actor context cannot access DRF serializer/view context directly.

Behavior
^^^^^^^^

``CurrentUserMiddleware`` wraps ``get_response`` in ``SetCurrentUser(request)``.

- enter: bind lazy callable returning ``request.user``
- exit: clear callable back to ``None``

Trade-offs
^^^^^^^^^^

- simple and low overhead,
- request-thread only,
- not async-context aware across asyncio task boundaries.

When not to use
^^^^^^^^^^^^^^^

If most writes happen outside request lifecycle, prefer explicit actor propagation.
This middleware is also a poor fit for async-heavy write paths where actor attribution depends on task-local context.


DebugMiddleware
---------------

Problem it solves
^^^^^^^^^^^^^^^^^

DRF default logging often misses request duration/query-count context at endpoint granularity.

Request phase
^^^^^^^^^^^^^

``process_request`` records:

- start timestamp,
- initial query count,
- method/path/user-agent/remote IP/query params in logs.

Response phase
^^^^^^^^^^^^^^

``process_response`` computes:

- duration,
- request-local query count delta,
- warning logs for slow requests and high query count using configurable thresholds,
- response headers ``X-Debug-Duration`` and ``X-Debug-Queries`` when logger category is enabled.

Exception phase
^^^^^^^^^^^^^^^

``process_exception`` logs request failure with elapsed duration and traceback.

Performance implications
^^^^^^^^^^^^^^^^^^^^^^^^

- minor CPU overhead for timing and logging calls,
- logging volume can become significant under high QPS if request category is enabled broadly.


SQLDebugMiddleware
------------------

Problem it solves
^^^^^^^^^^^^^^^^^

Need request-scoped SQL visibility without integrating external profiler tooling immediately.

Behavior
^^^^^^^^

- captures query list slice for current request,
- logs query count and total time,
- logs each SQL statement at debug level,
- warns when query exceeds ``DEBUG_SLOW_QUERY_THRESHOLD``.

Trade-offs
^^^^^^^^^^

- useful for diagnostics,
- can generate very large logs and sensitive query output if used carelessly in production.


ProfilerMiddleware
------------------

Problem it solves
^^^^^^^^^^^^^^^^^

Endpoint-level CPU hotspot diagnosis via cProfile without custom instrumentation in each view.

Enablement conditions
^^^^^^^^^^^^^^^^^^^^^

Enabled only when both are true:

- performance logger category is enabled,
- ``ENABLE_PROFILER`` setting is true.

Behavior
^^^^^^^^

- starts ``cProfile.Profile`` in request phase,
- stops and renders sorted stats in response phase,
- logs top functions using configured sort method and count.

When not to use
^^^^^^^^^^^^^^^

- high-throughput production traffic paths where profiling overhead is unacceptable,
- environments with strict log payload size constraints.


Compatibility and integration
-----------------------------

Recommended ordering (conceptual):

1. authentication middleware before ``CurrentUserMiddleware``,
2. debug middlewares after core Django middleware.

Example:

.. code-block:: python

   MIDDLEWARE = [
       "django.contrib.sessions.middleware.SessionMiddleware",
       "django.contrib.auth.middleware.AuthenticationMiddleware",
       "drf_commons.middlewares.current_user.CurrentUserMiddleware",
       "drf_commons.middlewares.debug.DebugMiddleware",
   ]

Migration strategy
------------------

1. enable ``CurrentUserMiddleware`` first (low observability noise),
2. enable ``DebugMiddleware`` in staging with conservative categories,
3. selectively enable SQL/profiler middleware for troubleshooting windows.

Alternative approaches
----------------------

- OpenTelemetry or APM agents for distributed tracing,
- explicit per-view instrumentation decorators only,
- DB-proxy level query analytics.

Architecture
============

This document describes how ``drf-commons`` components interact at runtime and what architectural constraints they impose.

Architectural Thesis
--------------------

The library is not a replacement for DRF. It is a collection of composition-oriented building blocks that enforce consistent behavior around:

- response envelopes,
- bulk endpoint mechanics,
- import/export workflows,
- request-scoped user context,
- category-aware observability.

The design preference is thin abstractions over DRF, with most policy encoded as mixin behavior plus settings-driven defaults.

Component Topology
------------------

Request-path components:

- ``middlewares.current_user`` and ``current_user.utils``
- ``views.mixins.*``
- ``serializers.*``
- ``models.*``
- ``response.utils``

Data pipeline components:

- ``services.import_from_file.*``
- ``services.export_file.*``
- ``services.management.commands.generate_import_template``

Observability components:

- ``debug.core.categories``
- ``debug.logger``
- ``debug.utils``
- ``debug.logging.*``
- ``decorators.*``
- ``middlewares.debug``

Cross-cutting configuration:

- ``common_conf.settings`` with ``COMMON_`` namespaced override precedence.

Request Lifecycle (Synchronous API Path)
----------------------------------------

Typical API call flow in a deployment using this library:

1. ``CurrentUserMiddleware`` binds ``request.user`` to thread-local accessor.
2. Optional debug middleware captures timing/query baselines.
3. View mixin executes CRUD/bulk/import/export behavior.
4. Serializers perform validation and representation.
5. Model mixins apply actor/timestamp/soft-delete/version logic where ``save()`` is used.
6. Response helper builds envelope with timestamp and success/error shape.
7. Middleware clears thread-local context and appends debug headers/logging if enabled.

Key constraint: thread-local actor propagation works only within the request thread lifecycle.

Write Path Architecture
-----------------------

The write stack uses layered responsibilities:

- views decide endpoint contract and list-vs-single update path,
- serializers decide field conversion and object validation,
- models enforce attribution/metadata policy on ``save``-based writes,
- service layer handles complex file-based ingestion/export outside serializer scope.

This separation is pragmatic but not strict domain-driven architecture. For large systems, a separate service/domain layer may still be required to centralize business invariants.

Import Architecture
-------------------

The import system is configuration-driven and staged:

1. config validation,
2. file parsing,
3. header strictness check,
4. lookup prefetch,
5. per-step model processing in declared order,
6. create/update persistence with fallback,
7. summary construction.

The pipeline is optimized for operational imports, not event-stream ingestion. It favors deterministic templates over flexible schema evolution.

Export Architecture
-------------------

Export flow is request-driven:

1. caller supplies selected fields and rows,
2. service normalizes rows and metadata,
3. format-specific exporter renders CSV/XLSX/PDF,
4. response is returned immediately.

This is suitable for interactive admin exports. For large batch reporting, async workflows are more appropriate.

Observability Architecture
--------------------------

Category gating is central:

- each logger call can be disabled by category,
- disabled categories receive a ``NullLogger`` and become no-op,
- production mode further restricts categories to configured safe subset.

Consequence:

- instrumentation call sites remain in business code without per-call ``if enabled`` checks,
- observability behavior is controlled from settings rather than code forks.

Configuration Architecture
--------------------------

``common_conf.settings`` resolves settings in order:

1. ``COMMON_<KEY>``
2. ``<KEY>``
3. default

This allows incremental adoption in legacy projects that already define similarly named global settings, while still encouraging namespaced configuration.

Architectural Trade-offs
------------------------

Strengths:

- low-friction DRF integration via mixins,
- strong reuse for repetitive API patterns,
- explicit, inspectable import/export behavior.

Constraints:

- middleware-coupled actor attribution,
- some high-throughput paths remain memory-heavy,
- bulk update safety depends on ID-based row mapping in view-layer orchestration,
- strict template coupling for import workflows.

When this architecture fits
---------------------------

- backend platforms with many similar CRUD resources,
- admin-heavy APIs requiring tabular import/export,
- teams that value consistent endpoint envelopes and operational tooling.

When to avoid broad adoption
----------------------------

- event-driven systems where request-thread context is not the dominant execution model,
- APIs requiring strict optimistic-concurrency semantics on every write,
- workflows requiring fully asynchronous, resumable large-scale data ingestion.

Adoption and migration strategy
-------------------------------

Recommended rollout sequence:

1. adopt response and pagination helpers first (low coupling),
2. add view mixins for new endpoints only,
3. introduce model mixins on selected models with explicit backfill plans,
4. add import/export for operational domains with clear runbooks,
5. finally enable debug/decorator instrumentation categories in controlled stages.

This sequence minimizes regression surface and keeps rollback simple.

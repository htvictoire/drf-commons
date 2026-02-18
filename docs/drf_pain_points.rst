DRF Pain Points and drf-commons Design Responses
================================================

This document focuses on architectural decision support for senior teams.
It answers four questions for each problem area:

- how DRF normally behaves,
- why that can be insufficient in production,
- what ``drf-commons`` changes,
- what risks/trade-offs remain.

1. Repetitive Endpoint Boilerplate
----------------------------------

Default DRF behavior

- CRUD endpoints are straightforward with ``ModelViewSet`` but teams still duplicate message formatting, envelope structure, and bulk endpoints.

Why this becomes insufficient

- large API surfaces drift in response shape and operator experience,
- cross-team consistency erodes when each viewset customizes contract independently.

``drf-commons`` response

- CRUD and bulk mixins provide reusable endpoint behavior,
- response helpers enforce consistent ``success/timestamp/message/data`` envelope.

Trade-offs and limits

- envelope consistency is not automatic for non-mixin endpoints,
- response body with 204 codes may conflict with strict HTTP clients.

Adoption guidance

- start with response helpers and CRUD mixins in new endpoints,
- migrate old endpoints behind versioned API boundaries.


2. Bulk Mutation Semantics
--------------------------

Default DRF behavior

- no single blessed approach for bulk create/update/delete.

Why this is insufficient

- teams implement ad hoc bulk logic with inconsistent validation and transactional behavior.

``drf-commons`` response

- dedicated bulk actions with size limits and structured responses,
- serializer base supports one-shot ``bulk_update``.

Trade-offs and limits

- bulk update row matching is now strict ID-based in view mixins, but direct list-serializer use still requires caller-supplied ID-aligned instances,
- bulk operations bypass model ``save()`` hooks/signals.

When not to use

- domains requiring per-row side effects or strict per-row audit hooks.

Alternative approach

- custom service layer bulk operations with explicit reconciliation and row-level status model.


3. Request-Scoped Current User in Models
----------------------------------------

Default DRF behavior

- actor propagation to model layer is manual.

Why this is insufficient

- serializer/view omissions cause silent audit gaps.

``drf-commons`` response

- thread-local current user utilities,
- middleware wiring,
- ``UserActionMixin`` and ``CurrentUserField`` integration.

Trade-offs and limits

- request-thread centric design,
- non-request execution contexts require explicit user seeding,
- middleware dependency enforced eagerly.

When not to use

- heavily async/event-driven architectures with no request context continuity.


4. Computed Ordering Across Related Fields
------------------------------------------

Default DRF behavior

- ordering filter supports declared fields but complex computed ordering patterns require custom logic.

Why this is insufficient

- front-end sortable columns often map to related or aggregate expressions.

``drf-commons`` response

- ``ComputedOrderingFilter`` + processors support string/list/aggregate mappings,
- annotations are applied only when needed.

Trade-offs and limits

- this is ordering-only, not full computed filtering DSL,
- unsupported mapping types fail at runtime.

Alternative

- per-view custom queryset/order logic when requirements are highly specialized.


5. Operational Import Pipelines
-------------------------------

Default DRF behavior

- serializers validate request payloads, but template-driven file import with multi-model dependencies is manual work.

Why this is insufficient

- production imports need strict schema control, reference resolution, transforms, and failure reporting.

``drf-commons`` response

- config validator + strict file reader + staged data processor,
- lookup prefetching, unique detection, batch create/update attempts,
- structured summary and row-level errors.

Trade-offs and limits

- strict headers reject extra columns,
- replace mode is strict all-or-nothing and returns 422 when any row fails,
- multi-step imports rely on row-level status/error tracking for final summary reporting.

When not to use

- unstructured third-party input feeds with frequent schema drift.

Alternative

- queue-backed ETL with schema registry and transformation pipeline.


6. Exporting Data for Operations and Reporting
----------------------------------------------

Default DRF behavior

- no built-in multi-format document export layer.

Why this is insufficient

- operational teams need consistent CSV/XLSX/PDF generation with labels, headers, and metadata.

``drf-commons`` response

- export service with reusable data processor and format exporters,
- supports alignment, common-value header extraction, titles, working date footer.

Trade-offs and limits

- fully in-memory export path,
- optional dependencies required for XLSX/PDF,
- some format edge cases (for example column-letter merge limits in XLSX exporter).

When not to use

- very large exports requiring stream-first or async artifact generation.

Alternative

- background report jobs and object storage delivery.


7. Debug and Observability Drift
--------------------------------

Default DRF behavior

- logging is framework-level; feature-level instrumentation is project-specific.

Why this is insufficient

- teams either over-log in production or under-observe critical paths.

``drf-commons`` response

- category-aware logging with production-safe category filtering,
- middleware and decorator instrumentation that no-ops when disabled.

Trade-offs and limits

- requires disciplined category configuration,
- logging output quality depends on consistent team usage patterns.

Alternative

- centralized observability stack with explicit tracing middleware and APM SDK.


Compatibility and Integration Summary
-------------------------------------

- core: Django >= 3.2, DRF >= 3.12
- optional: ``openpyxl``, ``weasyprint``, ``pandas``, ``django-constance`` depending on features
- best integrated in service-oriented DRF backends where operational data workflows are part of API responsibilities

Migration recommendation
------------------------

Adopt incrementally by concern:

1. response/pagination helpers,
2. CRUD and bulk mixins,
3. model attribution mixins,
4. import/export services,
5. debug categories and decorators.

This sequence gives fastest value with lowest regression risk.

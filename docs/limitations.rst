Limitations and Operational Constraints
=======================================

This page documents constraints observed from source code, not aspirational behavior.

Execution Model Constraints
---------------------------

Request-scoped user context
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- current-user propagation is thread-local and middleware-driven,
- thread-local storage does not propagate actor context across asyncio task switches,
- non-request contexts (tasks, management commands, signal handlers) do not automatically have actor context,
- model attribution logic that depends on current user can therefore produce null actor fields outside request flow.

Middleware coupling
^^^^^^^^^^^^^^^^^^^

- ``UserActionMixin`` and ``CurrentUserField`` rely on middleware dependency checks,
- missing middleware is treated as configuration error.
- model ``save()`` / field ``pre_save()`` paths using these components raise ``ImproperlyConfigured`` when the middleware dependency is absent.
- worker or script processes that load Django settings without the required middleware cannot use these write paths successfully.

Model and persistence constraints
---------------------------------

Soft delete scope
^^^^^^^^^^^^^^^^^

- soft delete is state mutation (``is_active``/``deleted_at``), not query policy,
- no default manager excludes soft-deleted rows.

Bulk operations bypass hooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- serializer bulk update and queryset-level bulk operations bypass model ``save()`` and signals,
- side-effect logic tied to save/signals will not run.

Import pipeline constraints
---------------------------

Header strictness
^^^^^^^^^^^^^^^^^

- import rejects files with missing or additional columns,
- Excel parsing assumes header row index 4 (fifth row).
- lookup fields must target concrete database fields on lookup models.

Replace mode transaction semantics
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- replace mode executes delete + import in one transaction,
- any failed imported rows roll back the replacement and preserve existing data,
- strict replacement requires zero failed rows to commit.

Row status semantics
^^^^^^^^^^^^^^^^^^^^

- failed row status is sticky across multi-step processing,
- update/create persistence failures are captured per row and reflected in ``errors``,
- summary counters are generated from the final per-row status set.
- duplicate ``unique_by`` keys in the same import chunk are not inserted as separate records.

Export pipeline constraints
---------------------------

Memory profile
^^^^^^^^^^^^^^

- export workflows operate on fully materialized data structures,
- not stream-oriented for very large datasets.

Format-specific limitations
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- PDF orientation logic is heuristic, not exact layout measurement.

API-contract quirks observed in current code
--------------------------------------------

- some ``FileExportMixin`` error branches pass ``status`` argument into ``error_response`` which expects ``status_code``,
- ``FileExportMixin`` validates ``includes`` and forwards it directly; client/server mismatch on string vs list can break column interpretation.
- list endpoints with ``?paginated=false`` serialize the full queryset into one response and can exhaust memory on high-cardinality datasets.

Repository-level caveats
------------------------

- ``pyproject.toml`` pytest settings module points to ``drf_commons.common_conf.test_settings`` while repository includes ``drf_commons/common_conf/django_settings.py``,

Dependency constraints
----------------------

- import requires ``pandas`` (and Excel engines for excel formats),
- XLSX export requires ``openpyxl``,
- PDF export requires ``weasyprint``,
- document header integration with ``constance`` is optional and handled with fallback.
- direct import of ``drf_commons.services.import_from_file`` without ``pandas`` raises ``ImportError``,
- import endpoints and ``generate_import_template`` command require import dependencies at time of use.

Mitigation strategy
-------------------

- add integration tests around your chosen subset of mixins/services,
- avoid assuming cross-feature transactional semantics unless verified,
- wrap high-risk paths (bulk import/export) with operational guardrails and rollback procedures.

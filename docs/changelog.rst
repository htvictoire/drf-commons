Changelog
=========

All notable changes to drf-commons are documented here.

drf-commons follows `Semantic Versioning <https://semver.org/>`_.

1.0.2 (Current)
----------------

*Maintenance release*

**Improvements**

* Replaced thread-local storage with ``ContextVar`` for request user management,
  ensuring ASGI compatibility and safe behavior in async contexts.
* Refactored bulk update to use ``QuerySet.bulk_update()`` by default, reducing
  database round-trips from O(n) to O(1) for bulk update operations.
* Introduced ``use_save_on_bulk_update`` flag for cases where signal-triggering
  individual saves are required.
* Refactored view mixins for cleaner composition and reduced coupling.
* Updated ``UserActionMixin`` to use context user resolution rather than
  serializer context threading.

**Fixes**

* Corrected ``BulkUpdateListSerializer`` behavior when incoming payload omits
  audit fields — defaults are now applied automatically.
* Fixed ``SoftDeleteMixin.is_deleted`` property to correctly reflect
  ``not self.is_active``.
* ``CurrentUserMiddleware`` now correctly handles both coroutine and non-coroutine
  handler functions.

1.0.0
-----

*Initial production release*

**New Features**

* ``BaseModelMixin`` — Composable base model with UUID PK, timestamps, user tracking,
  soft delete, and JSON serialization.
* ``BaseViewSet`` — Pre-composed full CRUD + export ViewSet.
* ``BulkViewSet`` — CRUD + bulk create/update/delete + export.
* ``BaseModelSerializer`` — Atomic write handling with relational ordering.
* Configurable serializer field system — 20+ field types covering all
  foreign key and many-to-many access patterns.
* ``success_response`` / ``error_response`` — Standardized JSON response envelope.
* ``CurrentUserMiddleware`` — Async-safe context user injection.
* ``FileImportService`` — Multi-model CSV/XLSX import pipeline.
* ``ExportService`` — CSV, XLSX, PDF export.
* ``StandardPageNumberPagination`` / ``LimitOffsetPaginationWithFormat``.
* ``ComputedOrderingFilter`` — Ordering on annotated/computed fields.
* ``StructuredLogger`` — Category-based structured logging.
* ``SQLDebugMiddleware``, ``ProfilerMiddleware`` — Development debug middleware.
* ``cache_debug``, ``api_request_logger``, ``log_function_call``,
  ``log_exceptions``, ``log_db_query``, ``api_performance_monitor`` decorators.
* ``VersionMixin`` — Optimistic locking with ``VersionConflictError``.
* ``SlugMixin`` — Deterministic slug generation with collision avoidance.
* ``MetaMixin`` — Metadata, tags, and notes on any model.
* ``IdentityMixin``, ``AddressMixin`` — Person and address field sets.
* ``MiddlewareChecker`` — Runtime middleware validation.
* Startup-time ``ImproperlyConfigured`` raise when ``CurrentUserMiddleware``
  is missing but required by installed models.
* Test infrastructure: ``UserFactory``, ``APIRequestFactoryWithUser``.
* Management command: ``generate_import_template``.

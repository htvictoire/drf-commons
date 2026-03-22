# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The full changelog is also available in the
[ReadTheDocs documentation](https://drf-commons.readthedocs.io/en/latest/changelog.html).

---

## [Unreleased]

---

## [1.0.3b1] - 2026-03-21

### Added

- CI test workflow (`tests.yml`) running pytest across Python 3.10–3.12 and
  Django 4.2–5.1 on every push and pull request, with 85% coverage threshold.
- Coverage and CI status badges added to README.
- Tests consolidated into top-level `tests/` directory for discoverability.
- `CHANGELOG.md` at project root (this file), aligned with `docs/changelog.rst`.
- `CONTRIBUTING.md` at project root with commit conventions and PR checklist.
- `make release` target with pre-release checklist.
- Versioning rules and release checklist documented in `PUBLISHING.md`.

### Changed

- Removed overreaching maturity claims from README opening line and
  `pyproject.toml` description. Package classifier already reflects Beta status.
- Replaced outdated manual Twine publishing instructions with a pointer to the
  automated CI release process.

---

## [1.0.2] - 2025-12-01

*Maintenance release*

### Changed

- Replaced thread-local storage with `ContextVar` for request user management,
  ensuring ASGI compatibility and safe behavior in async contexts.
- Refactored bulk update to use `QuerySet.bulk_update()` by default, reducing
  database round-trips from O(n) to O(1) for bulk update operations.
- Introduced `use_save_on_bulk_update` flag for cases where signal-triggering
  individual saves are required.
- Refactored view mixins for cleaner composition and reduced coupling.
- Updated `UserActionMixin` to use context user resolution rather than
  serializer context threading.

### Fixed

- Corrected `BulkUpdateListSerializer` behavior when incoming payload omits
  audit fields — defaults are now applied automatically.
- Fixed `SoftDeleteMixin.is_deleted` property to correctly reflect
  `not self.is_active`.
- `CurrentUserMiddleware` now correctly handles both coroutine and
  non-coroutine handler functions.

---

## [1.0.0] - 2025-11-01

*Initial release*

### Added

- `BaseModelMixin` — Composable base model with UUID PK, timestamps, user
  tracking, soft delete, and JSON serialization.
- `BaseViewSet` — Pre-composed full CRUD + export ViewSet.
- `BulkViewSet` — CRUD + bulk create/update/delete + export.
- `BaseModelSerializer` — Atomic write handling with relational ordering.
- Configurable serializer field system — 20+ field types covering all
  foreign key and many-to-many access patterns.
- `success_response` / `error_response` — Standardized JSON response envelope.
- `CurrentUserMiddleware` — Async-safe context user injection.
- `FileImportService` — Multi-model CSV/XLSX import pipeline.
- `ExportService` — CSV, XLSX, PDF export.
- `StandardPageNumberPagination` / `LimitOffsetPaginationWithFormat`.
- `ComputedOrderingFilter` — Ordering on annotated/computed fields.
- `StructuredLogger` — Category-based structured logging.
- `SQLDebugMiddleware`, `ProfilerMiddleware` — Development debug middleware.
- `cache_debug`, `api_request_logger`, `log_function_call`, `log_exceptions`,
  `log_db_query`, `api_performance_monitor` decorators.
- `VersionMixin` — Optimistic locking with `VersionConflictError`.
- `SlugMixin` — Deterministic slug generation with collision avoidance.
- `MetaMixin` — Metadata, tags, and notes on any model.
- `IdentityMixin`, `AddressMixin` — Person and address field sets.
- `MiddlewareChecker` — Runtime middleware validation.
- Startup-time `ImproperlyConfigured` raise when `CurrentUserMiddleware`
  is missing but required by installed models.
- Test infrastructure: `UserFactory`, `APIRequestFactoryWithUser`.
- Management command: `generate_import_template`.

---

[Unreleased]: https://github.com/htvictoire/drf-commons/compare/v1.0.3b1...HEAD
[1.0.3b1]: https://github.com/htvictoire/drf-commons/compare/v1.0.2...v1.0.3b1
[1.0.2]: https://github.com/htvictoire/drf-commons/compare/v1.0.0...v1.0.2
[1.0.0]: https://github.com/htvictoire/drf-commons/releases/tag/v1.0.0

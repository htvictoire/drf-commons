Architecture
============

drf-commons is organized as a structural layer composed atop Django REST
Framework's own extension points. Understanding this architecture is essential
for effective integration and extension.

System Layers
-------------

drf-commons maps to a clean vertical slice of a DRF-based application:

.. code-block:: text

   ┌─────────────────────────────────────────────┐
   │               HTTP Request                  │
   └──────────────────────┬──────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────┐
   │            Middleware Layer                  │
   │  CurrentUserMiddleware                       │
   │  SQLDebugMiddleware  ProfilerMiddleware       │
   └──────────────────────┬──────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────┐
   │              View Layer                      │
   │  BaseViewSet  BulkViewSet  ReadOnlyViewSet   │
   │  ImportableViewSet  BulkImportableViewSet    │
   │  (CRUD / Bulk / Import / Export Mixins)      │
   └──────────────────────┬──────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────┐
   │           Serializer Layer                   │
   │  BaseModelSerializer                        │
   │  BulkUpdateListSerializer                   │
   │  ConfigurableRelatedField variants           │
   └──────────────────────┬──────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────┐
   │             Model Layer                      │
   │  BaseModelMixin  TimeStampMixin             │
   │  UserActionMixin  SoftDeleteMixin           │
   │  VersionMixin  SlugMixin  MetaMixin          │
   │  IdentityMixin  AddressMixin                │
   └──────────────────────┬──────────────────────┘
                          │
   ┌──────────────────────▼──────────────────────┐
   │           Service Layer                      │
   │  ExportService  FileImportService            │
   └─────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────┐
   │         Cross-Cutting Concerns               │
   │  Context User (ContextVar)                  │
   │  StructuredLogger  Debug Utilities           │
   │  Decorators  Pagination  Filters             │
   └─────────────────────────────────────────────┘

Package Structure
-----------------

.. code-block:: text

   drf_commons/
   ├── apps.py                    # Django AppConfig — startup validation
   ├── __init__.py                # Package version export
   │
   ├── common_conf/               # Configuration management
   │   ├── settings.py            # CommonSettings — COMMON namespace resolution
   │   ├── django_settings.py     # Test Django configuration
   │   └── test_urls.py / test_views.py
   │
   ├── current_user/              # ContextVar-based user management
   │   └── utils.py
   │
   ├── models/                    # Model mixins and fields
   │   ├── base.py                # BaseModelMixin + composition mixins
   │   ├── mixins.py              # JsonModelMixin
   │   ├── content.py             # SlugMixin, MetaMixin, VersionMixin
   │   ├── person.py              # IdentityMixin, AddressMixin
   │   └── fields.py             # CurrentUserField
   │
   ├── views/                     # ViewSet classes and action mixins
   │   ├── base.py               # Pre-composed ViewSet classes
   │   └── mixins/
   │       ├── crud.py           # CRUD action mixins
   │       ├── bulk.py           # Bulk operation mixins
   │       ├── import_export.py  # File import/export mixins
   │       └── shared.py         # Shared mixin utilities
   │
   ├── serializers/               # Serializer and field system
   │   ├── base.py               # BaseModelSerializer, BulkUpdateListSerializer
   │   └── fields/
   │       ├── base.py           # ConfigurableRelatedField base classes
   │       ├── single.py         # Single relation field variants
   │       ├── many.py           # Many-to-many field variants
   │       ├── readonly.py       # Read-only field variants
   │       ├── custom.py         # Custom output field
   │       └── mixins/           # Field behaviour mixins
   │
   ├── middlewares/               # Django middleware
   │   ├── current_user.py       # CurrentUserMiddleware (sync/async)
   │   └── debug.py              # Debug/profiling middleware
   │
   ├── pagination/                # Pagination classes
   │   └── base.py
   │
   ├── filters/                   # Filter backends
   │   └── ordering/
   │       └── computed.py       # ComputedOrderingFilter
   │
   ├── response/                  # Response utilities
   │   └── utils.py              # success_response, error_response
   │
   ├── decorators/                # Function/method decorators
   │   ├── cache.py
   │   ├── logging.py
   │   ├── database.py
   │   └── performance.py
   │
   ├── services/                  # Business logic services
   │   ├── export_file/          # Multi-format export service
   │   └── import_from_file/     # Multi-model import service
   │
   ├── debug/                     # Debug and observability
   │   ├── logger.py             # StructuredLogger
   │   └── utils.py              # Debug utilities
   │
   └── utils/                     # Internal utilities
       └── middleware_checker.py

Design Decisions
----------------

ContextVar for User Resolution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Standard DRF patterns for tracking the current user involve threading request
context through serializer ``context`` dictionaries. This pattern is:

* **Fragile** — requires every serializer in the chain to explicitly pass context
* **Async-unsafe** — thread-local storage breaks under concurrent async tasks
* **Boilerplate-heavy** — creates coupling between serializer and view layers

drf-commons uses Python's :class:`contextvars.ContextVar`, introduced in
Python 3.7 and designed precisely for this use case. ``CurrentUserMiddleware``
sets the user into the context variable at request start and resets it at
request end. The context is correctly scoped to each coroutine in async
deployments.

.. code-block:: python

   # Internal implementation (simplified)
   _current_user: ContextVar[Optional[AbstractBaseUser]] = ContextVar(
       "_current_user", default=None
   )

   def get_current_user():
       return _current_user.get()

Mixin Composition at Every Layer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every drf-commons component is a mixin, not a base class. This means:

* **ViewSets** are explicit compositions of action mixins
* **Model classes** are explicit compositions of field/behavior mixins
* **Serializers** compose field types from the configurable field system

This pattern makes the behavior of each class fully visible at its definition
site. A developer reading ``class BulkViewSet`` immediately sees every action
it provides through its MRO.

Transaction Safety by Default
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`~drf_commons.serializers.base.BaseModelSerializer` wraps all write
operations in ``django.db.transaction.atomic()``. Bulk operations in
:class:`~drf_commons.views.mixins.bulk.BulkCreateModelMixin` and
:class:`~drf_commons.views.mixins.bulk.BulkUpdateModelMixin` are also wrapped
in atomic blocks. This ensures partial writes are never committed.

Batch-Size-Aware Bulk Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Bulk operation mixins read batch size from the ``COMMON`` settings namespace
at runtime. This allows operators to tune batch sizes per environment without
code changes. The viewset's ``bulk_batch_size`` attribute overrides the global
setting when set, allowing per-resource tuning.

Lazy Optional Dependency Loading
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Export and import services use lazy imports:

.. code-block:: python

   def export_xlsx(self, data):
       try:
           import openpyxl
       except ImportError:
           raise ImproperlyConfigured(
               "Install drf-commons[export] to use XLSX export."
           )

This keeps the core package installable without any optional dependencies and
produces actionable error messages when a feature is used without its
dependencies installed.

Startup-Time Validation
~~~~~~~~~~~~~~~~~~~~~~~~

The :class:`~drf_commons.apps.DrfCommonsConfig` ``ready()`` method invokes
:func:`~drf_commons.utils.middleware_checker.enforce_current_user_middleware_if_used`.
This function inspects the application's installed models and raises
:class:`django.core.exceptions.ImproperlyConfigured` at startup if:

* Any model uses :class:`~drf_commons.models.base.UserActionMixin` or
  :class:`~drf_commons.models.fields.CurrentUserField`
* ``CurrentUserMiddleware`` is not present in ``MIDDLEWARE``

This surfaces configuration errors at startup rather than at the first API
request, a significantly better debugging experience.

Extension Points
----------------

drf-commons is designed to be extended at every layer:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Component
     - Extension Point
   * - ViewSets
     - Compose custom mixins with ``GenericViewSet``
   * - Model Mixins
     - Subclass and override ``save()``, ``soft_delete()``, etc.
   * - Serializer Fields
     - Subclass ``ConfigurableRelatedField``, implement abstract methods
   * - Response Format
     - Override ``success_response`` / ``error_response`` functions
   * - Import Config
     - Provide ``import_transforms`` dict for custom field transformations
   * - Export Config
     - Provide ``export_field_config`` dict and ``column_config`` per export
   * - Pagination
     - Subclass ``StandardPageNumberPagination``, override ``page_size``
   * - Ordering
     - Add ``computed_ordering_fields`` dict to ViewSet for annotated ordering
   * - Logging
     - Subclass ``StructuredLogger`` or use decorator variants

See :doc:`extensibility` for detailed extension recipes.

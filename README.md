# drf-commons

[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-3.2%2B-green.svg)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/djangorestframework-3.12%2B-red.svg)](https://www.django-rest-framework.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/badge/pypi-v1.0.1-blue.svg)](https://pypi.org/project/drf-commons/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**drf-commons** is a production-grade utility library for Django REST Framework that eliminates architectural repetition, enforces API consistency, and provides composable abstractions for building scalable, maintainable REST APIs at any scale.

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [What drf-commons Solves](#what-drf-commons-solves)
- [Feature Overview](#feature-overview)
- [Architecture Philosophy](#architecture-philosophy)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Before vs After](#before-vs-after)
- [Core Components](#core-components)
  - [Model Mixins](#model-mixins)
  - [View Layer](#view-layer)
  - [Serializer System](#serializer-system)
  - [Response Standardization](#response-standardization)
  - [Bulk Operations](#bulk-operations)
  - [Import / Export Services](#import--export-services)
  - [Middleware & Context](#middleware--context)
  - [Decorators](#decorators)
  - [Pagination & Filtering](#pagination--filtering)
  - [Debug & Observability](#debug--observability)
- [Design Principles](#design-principles)
- [Production Usage](#production-usage)
- [Extensibility](#extensibility)
- [Performance Considerations](#performance-considerations)
- [Use Cases](#use-cases)
- [Engineering Capabilities Demonstrated](#engineering-capabilities-demonstrated)
- [Contributing](#contributing)
- [License](#license)

---

## Why This Exists

Django REST Framework is a powerful toolkit that excels at the fundamentals of REST API construction. However, production API development at scale consistently exposes structural limitations that DRF does not address out of the box:

### The Structural Problems with Vanilla DRF

**Inconsistent Response Envelopes**

DRF returns raw serialized data with no standard envelope. In a production system with multiple teams, endpoints return data in structurally inconsistent forms — some wrap in `{"data": ...}`, others return arrays, others return flat objects. Clients cannot rely on a predictable contract.

**Repetitive ViewSet Patterns**

Every resource requires the same boilerplate: permission classes, serializer resolution, queryset filtering, pagination integration, error handling. In a system with 50+ resources, this is thousands of lines of structural duplication.

**No Audit Trail**

DRF has no built-in mechanism for tracking who created or last modified a record. The common workarounds (request context passing, serializer overrides) are fragile and scatter responsibility across layers.

**Primitive Bulk Operation Support**

Bulk create, update, and delete are not first-class citizens in DRF. Rolling your own bulk operations means reimplementing transaction safety, validation, and audit population for each resource — often inconsistently.

**Unsafe Thread-Local User Storage**

The standard pattern of storing the current user in thread-local storage (`threading.local()`) breaks in async environments. With ASGI becoming the deployment standard, thread-local user storage introduces subtle bugs that are difficult to diagnose.

**Rigid Serializer Field Behavior**

DRF's relational fields are write-as-ID, read-as-ID. Representing the same relation differently depending on context (ID write / nested read, or nested write / ID read) requires custom field classes every time — a disproportionate amount of code for a common requirement.

**No Built-In Import/Export**

Data import from CSV/XLSX and export to multiple formats are universally required in production systems but completely absent from DRF's scope.

**Scattered Debug Tooling**

Query counting, slow request detection, SQL profiling, and structured logging require third-party packages assembled without coherence.

---

## What drf-commons Solves

`drf-commons` is not a framework on top of DRF — it is a **structural layer** composed atop DRF internals. It follows the principle of progressive enhancement: you adopt what you need, it composes with what you have, and it never breaks what DRF already provides.

| Problem | drf-commons Solution |
|---|---|
| Inconsistent responses | `success_response()` / `error_response()` with ISO8601 timestamps |
| Repetitive viewset boilerplate | Pre-composed ViewSet classes (`BaseViewSet`, `BulkViewSet`, etc.) |
| No audit trail | `UserActionMixin` + `CurrentUserMiddleware` + ContextVar-based user resolution |
| Unsafe thread-local user | `ContextVar`-based `get_current_user()` with async support |
| Primitive bulk operations | `BulkCreateModelMixin`, `BulkUpdateModelMixin`, `BulkDeleteModelMixin` with transaction safety |
| Rigid serializer fields | 20+ configurable field types (`IdToDataField`, `FlexibleField`, etc.) |
| No import/export | `FileImportService`, `ExportService` with CSV/XLSX/PDF support |
| Scattered debug tooling | Unified `StructuredLogger`, `SQLDebugMiddleware`, performance decorators |
| Soft delete complexity | `SoftDeleteMixin` with `soft_delete()`, `restore()` |
| No optimistic locking | `VersionMixin` with conflict detection |

---

## Feature Overview

### Model Layer
- `BaseModelMixin` — UUID PK, timestamps, soft delete, audit trail, JSON serialization
- `TimeStampMixin` — `created_at`, `updated_at` auto-population
- `UserActionMixin` — `created_by`, `updated_by` auto-population from request context
- `SoftDeleteMixin` — Non-destructive deletion with restore capability
- `VersionMixin` — Optimistic locking with `VersionConflictError`
- `SlugMixin` — Deterministic slug generation with collision avoidance
- `MetaMixin` — `metadata` JSONField, `tags`, `notes` with helper methods
- `IdentityMixin` — Person identity fields with computed properties
- `AddressMixin` — Structured address fields with coordinate support
- `CurrentUserField` — ForeignKey auto-populated from request context

### View Layer
- `BaseViewSet` — Full CRUD with file export
- `BulkViewSet` — CRUD + bulk create/update/delete
- `ReadOnlyViewSet`, `CreateListViewSet` — Restricted resource access patterns
- `ImportableViewSet`, `BulkImportableViewSet` — File import-capable viewsets
- Configurable `return_data_on_create`, `return_data_on_update`
- Optional `append_indexes` for sequentially numbered list results

### Serializer System
- `BaseModelSerializer` — Handles complex relational write patterns atomically
- `BulkUpdateListSerializer` — Efficient bulk updates via `bulk_update()`
- 20+ configurable field types covering all relation access patterns
- `FlexibleField` — Auto-detects input format, returns configured output

### Bulk Operations
- `BulkCreateModelMixin` — Atomic bulk creation with validation
- `BulkUpdateModelMixin` — Efficient `bulk_update()` or individual save modes
- `BulkDeleteModelMixin` — Bulk delete + bulk soft delete with missing ID reporting

### Import / Export
- `FileImportService` — Multi-model CSV/XLSX imports with transformation hooks
- `ExportService` — CSV, XLSX, PDF export
- `FileImportMixin`, `FileExportMixin` — ViewSet-level integration
- Management command: `generate_import_template`

### Infrastructure
- `CurrentUserMiddleware` — Async/sync middleware for ContextVar user injection
- `StructuredLogger` — Category-based structured logging
- `SQLDebugMiddleware`, `ProfilerMiddleware` — Development debug tooling
- `StandardPageNumberPagination`, `LimitOffsetPaginationWithFormat`
- `ComputedOrderingFilter` — Ordering on annotated/computed fields
- `cache_debug`, `api_request_logger`, `log_db_query`, `api_performance_monitor` decorators
- `MiddlewareChecker` — Runtime middleware validation

---

## Architecture Philosophy

`drf-commons` is built on three foundational principles:

**1. Composition Over Inheritance**

All components are designed as mixins. `BaseViewSet` is `CreateModelMixin + ListModelMixin + RetrieveModelMixin + UpdateModelMixin + DestroyModelMixin + FileExportMixin`. You can compose exactly the combination you need rather than inheriting a monolith.

**2. Explicit Over Implicit**

The library never silently modifies behavior. Every enhancement (audit tracking, response formatting, bulk operations) is a conscious integration choice. Configuration is explicit and overridable at every layer.

**3. Framework-Aligned, Not Framework-Replacing**

`drf-commons` works with DRF's internal dispatch, serializer resolution, and authentication layers. It does not subvert DRF internals — it extends them using DRF's own documented extension points.

---

## Installation

### Core Installation

```bash
pip install drf-commons
```

### With Optional Feature Sets

```bash
# File export support (CSV, XLSX, PDF)
pip install drf-commons[export]

# File import support (CSV, XLS, XLSX via pandas)
pip install drf-commons[import]

# Debug and profiling utilities
pip install drf-commons[debug]

# All optional features
pip install drf-commons[export,import,debug]
```

### Django Configuration

```python
# settings.py
INSTALLED_APPS = [
    ...
    'drf_commons',
    ...
]

MIDDLEWARE = [
    ...
    'drf_commons.middlewares.CurrentUserMiddleware',
    ...
]

# Optional: override drf-commons defaults
COMMON = {
    'BULK_OPERATION_BATCH_SIZE': 1000,
    'IMPORT_BATCH_SIZE': 250,
    'DEBUG_SLOW_REQUEST_THRESHOLD': 1.0,
    'DEBUG_HIGH_QUERY_COUNT_THRESHOLD': 10,
}
```

---

## Quickstart

### 1. Define a model using drf-commons mixins

```python
from django.db import models
from drf_commons.models import BaseModelMixin

class Article(BaseModelMixin):
    title = models.CharField(max_length=255)
    content = models.TextField()
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
```

`BaseModelMixin` provides: UUID primary key, `created_at`, `updated_at`, `created_by`, `updated_by`, `is_active`, `deleted_at`, and `get_json()`.

### 2. Define a serializer

```python
from drf_commons.serializers import BaseModelSerializer
from drf_commons.serializers.fields import IdToDataField

class ArticleSerializer(BaseModelSerializer):
    author = IdToDataField(queryset=User.objects.all(), serializer=UserSerializer)

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'published', 'author', 'created_at']
```

### 3. Define a viewset

```python
from drf_commons.views import BaseViewSet

class ArticleViewSet(BaseViewSet):
    queryset = Article.objects.filter(is_active=True)
    serializer_class = ArticleSerializer

    # Optional: configure bulk operations
    bulk_batch_size = 500

    # Optional: configure export
    export_field_config = {
        'title': 'Title',
        'content': 'Content',
        'published': 'Published',
    }
```

### 4. Register routes

```python
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet

router = DefaultRouter()
router.register('articles', ArticleViewSet, basename='article')
urlpatterns = router.urls
```

This gives you: `GET /articles/`, `POST /articles/`, `GET /articles/{id}/`, `PUT/PATCH /articles/{id}/`, `DELETE /articles/{id}/`, `POST /articles/export/`.

---

## Before vs After

### Response Standardization

**Before (vanilla DRF)**
```python
class ArticleViewSet(ViewSet):
    def list(self, request):
        articles = Article.objects.all()
        serializer = ArticleSerializer(articles, many=True)
        return Response(serializer.data)  # raw list, no envelope

    def create(self, request):
        serializer = ArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)  # inconsistent shape
```

**After (drf-commons)**
```python
class ArticleViewSet(BaseViewSet):
    queryset = Article.objects.filter(is_active=True)
    serializer_class = ArticleSerializer
    # All responses automatically formatted:
    # {"success": true, "timestamp": "...", "data": [...], "message": "..."}
```

---

### Audit Tracking

**Before (vanilla DRF)**
```python
class ArticleSerializer(ModelSerializer):
    def create(self, validated_data):
        # must manually inject request context
        request = self.context.get('request')
        validated_data['created_by'] = request.user
        validated_data['updated_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)
```

**After (drf-commons)**
```python
class Article(BaseModelMixin):
    title = models.CharField(max_length=255)
    # created_by, updated_by populated automatically via ContextVar
    # No serializer override required
```

---

### Bulk Operations

**Before (vanilla DRF)**
```python
@action(detail=False, methods=['post'])
def bulk_create(self, request):
    serializer = ArticleSerializer(data=request.data, many=True)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                instances = [Article(**item) for item in serializer.validated_data]
                Article.objects.bulk_create(instances)
        except Exception as e:
            return Response({'error': str(e)}, status=500)
        return Response({'created': len(instances)}, status=201)
    return Response(serializer.errors, status=400)
```

**After (drf-commons)**
```python
class ArticleViewSet(BulkViewSet):
    queryset = Article.objects.filter(is_active=True)
    serializer_class = ArticleSerializer
    # POST /articles/bulk-create/ — handled automatically
    # PUT  /articles/bulk-update/ — handled automatically
    # DELETE /articles/bulk-delete/ — handled automatically
```

---

### Serializer Relational Fields

**Before (vanilla DRF)**
```python
class ArticleSerializer(ModelSerializer):
    # Can't read nested author data while writing by ID without custom field
    author_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )
    author = UserSerializer(read_only=True)

    def to_representation(self, instance):
        # Override needed to conditionally show nested data
        ...
```

**After (drf-commons)**
```python
class ArticleSerializer(BaseModelSerializer):
    author = IdToDataField(queryset=User.objects.all(), serializer=UserSerializer)
    # Write: accept user ID
    # Read: return full nested UserSerializer output
```

---

## Core Components

### Model Mixins

#### `BaseModelMixin`

The canonical base model providing UUID primary key, timestamping, user action tracking, soft deletion, and JSON serialization.

```python
from drf_commons.models import BaseModelMixin

class Product(BaseModelMixin):
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=64, unique=True)
```

Provides:
- `id` — UUID primary key
- `created_at`, `updated_at` — ISO8601 timestamps (auto-populated)
- `created_by`, `updated_by` — ForeignKey to `AUTH_USER_MODEL` (auto-populated from request context)
- `is_active` — Soft delete flag
- `deleted_at` — Soft delete timestamp
- `get_json(**kwargs)` — Flexible JSON serialization

#### `VersionMixin`

Implements optimistic locking for high-concurrency write scenarios.

```python
from drf_commons.models.content import VersionMixin

class Document(BaseModelMixin, VersionMixin):
    body = models.TextField()
```

On concurrent modification:
```python
# Raises drf_commons.models.content.VersionConflictError
doc.increment_version()
doc.save()
```

#### `SlugMixin`

Auto-generates URL-safe slugs with deterministic collision avoidance.

```python
class Category(BaseModelMixin, SlugMixin):
    name = models.CharField(max_length=255)

    def get_slug_source(self):
        return self.name
    # Generates: "product-category", "product-category-1", etc.
```

---

### View Layer

#### Pre-composed ViewSets

| Class | Actions |
|---|---|
| `BaseViewSet` | CRUD + export |
| `BulkViewSet` | CRUD + bulk create/update/delete + export |
| `ReadOnlyViewSet` | List + retrieve + export |
| `CreateListViewSet` | Create + list + export |
| `BulkCreateViewSet` | Bulk create only |
| `BulkUpdateViewSet` | Bulk update only |
| `BulkDeleteViewSet` | Bulk delete only |
| `BulkOnlyViewSet` | All bulk operations |
| `ImportableViewSet` | CRUD + file import + export |
| `BulkImportableViewSet` | CRUD + bulk ops + file import + export |

```python
from drf_commons.views import BulkViewSet

class OrderViewSet(BulkViewSet):
    queryset = Order.objects.select_related('customer', 'items')
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = OrderFilterSet
```

---

### Serializer System

#### `BaseModelSerializer`

Extends DRF's `ModelSerializer` with:
- Atomic transaction wrapping for all writes
- `root_first` relation write ordering (write parent, then set FK on children)
- `dependency_first` relation write ordering (resolve dependencies before root)

```python
from drf_commons.serializers import BaseModelSerializer

class InvoiceSerializer(BaseModelSerializer):
    line_items = LineItemSerializer(many=True)

    class Meta:
        model = Invoice
        fields = ['id', 'customer', 'line_items', 'total']
```

#### Configurable Field Types

| Field | Write Input | Read Output |
|---|---|---|
| `IdToDataField` | ID | Nested serializer data |
| `IdToStrField` | ID | String representation |
| `DataToIdField` | Nested data | ID |
| `DataToStrField` | Nested data | String |
| `DataToDataField` | Nested data | Nested data |
| `StrToDataField` | String lookup | Nested data |
| `IdOnlyField` | ID | ID |
| `StrOnlyField` | String | String |
| `FlexibleField` | ID or string | Nested data |
| `ReadOnlyDataField` | N/A | Nested data |

Many-to-many variants: `ManyIdToDataField`, `ManyDataToIdField`, `ManyStrToDataField`, `ManyIdOnlyField`, `ManyFlexibleField`.

---

### Response Standardization

All viewset responses are automatically wrapped in a standardized envelope:

```python
# Success
{
    "success": true,
    "timestamp": "2024-01-15T10:30:00.000000Z",
    "message": "Operation completed successfully.",
    "data": { ... }
}

# Error
{
    "success": false,
    "timestamp": "2024-01-15T10:30:00.000000Z",
    "message": "Validation failed.",
    "errors": { "field": ["error message"] },
    "data": null
}
```

Use directly in custom views:

```python
from drf_commons.response import success_response, error_response

def my_view(request):
    return success_response(data={'key': 'value'}, message='Done.')
    return error_response(message='Not found.', status_code=404)
```

---

### Bulk Operations

#### `BulkUpdateModelMixin`

Supports two modes controlled by `use_save_on_bulk_update`:

**Default mode (`use_save_on_bulk_update = False`)** — Uses `QuerySet.bulk_update()` for maximum database efficiency. Audit fields (`updated_at`, `updated_by`) are automatically populated when not present in the payload.

**Save mode (`use_save_on_bulk_update = True`)** — Calls `instance.save()` on each object. Use when `save()` signal logic is required.

```python
class ProductViewSet(BulkViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    use_save_on_bulk_update = False  # default: bulk_update()
    bulk_batch_size = 500
```

#### `BulkDeleteModelMixin`

Returns a detailed deletion report:

```json
{
    "success": true,
    "data": {
        "requested_count": 10,
        "count": 8,
        "missing_ids": ["uuid-1", "uuid-2"]
    }
}
```

---

### Import / Export Services

#### File Export

```python
class ReportViewSet(BaseViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    export_field_config = {
        'title': 'Report Title',
        'created_at': 'Date Created',
        'status': 'Status',
    }
    # POST /reports/export/
    # Body: {"file_type": "xlsx", "includes": ["title", "status"]}
```

#### File Import

```python
class EmployeeViewSet(ImportableViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer

    import_file_config = {
        'file_format': 'xlsx',
        'order': ['department', 'employee'],
        'models': {
            'department': {
                'model': Department,
                'fields': ['name', 'code'],
                'unique_fields': ['code'],
            },
            'employee': {
                'model': Employee,
                'fields': ['first_name', 'last_name', 'email', 'department_code'],
                'unique_fields': ['email'],
                'foreign_keys': {
                    'department': {'model': Department, 'lookup_field': 'code', 'source_field': 'department_code'}
                }
            }
        }
    }
    # POST /employees/import-from-file/
    # Form: file=<file>, append_data=true
```

Generate an import template:

```bash
python manage.py generate_import_template EmployeeViewSet
```

---

### Middleware & Context

#### `CurrentUserMiddleware`

Injects the authenticated request user into Python's `ContextVar` for the duration of each request, enabling automatic `created_by`/`updated_by` population at the model layer without serializer context threading.

```python
# settings.py
MIDDLEWARE = [
    ...
    'drf_commons.middlewares.CurrentUserMiddleware',
    ...
]
```

Supports both WSGI (sync) and ASGI (async) deployments. Uses `contextvars.ContextVar` — safe across coroutines in async contexts.

#### Context User API

```python
from drf_commons.current_user import get_current_user, get_current_authenticated_user

user = get_current_user()           # Returns User or None
user = get_current_authenticated_user()  # Returns User or raises if anonymous
```

---

### Decorators

```python
from drf_commons.decorators import (
    api_request_logger,
    log_function_call,
    log_exceptions,
    log_db_query,
    api_performance_monitor,
    cache_debug,
)

@api_request_logger(log_body=True, log_headers=False)
@api_performance_monitor()
def my_api_view(request):
    ...

@log_db_query(query_type='read')
def fetch_heavy_data():
    ...

@log_function_call(logger_name='billing', log_args=True, log_result=True)
@log_exceptions(reraise=True)
def process_payment(order_id, amount):
    ...
```

---

### Pagination & Filtering

```python
from drf_commons.pagination import StandardPageNumberPagination, LimitOffsetPaginationWithFormat
from drf_commons.filters import ComputedOrderingFilter

class ArticleViewSet(BaseViewSet):
    pagination_class = StandardPageNumberPagination  # page_size=20, max=100
    filter_backends = [ComputedOrderingFilter]

    ordering_fields = ['title', 'created_at']
    computed_ordering_fields = {
        'comment_count': Count('comments'),   # Annotates and orders by aggregate
    }
```

---

### Debug & Observability

```python
from drf_commons.debug import StructuredLogger

logger = StructuredLogger('myapp')

logger.log_user_action(user=request.user, action='UPDATE', resource='Article', details={'id': article.id})
logger.log_api_request(request=request, response=response, duration=0.145)
logger.log_performance(operation='bulk_import', duration=2.3, details={'rows': 5000})
```

Enable debug middleware for development:

```python
# settings.py (development only)
MIDDLEWARE += [
    'drf_commons.middlewares.SQLDebugMiddleware',
    'drf_commons.middlewares.ProfilerMiddleware',
]
```

---

## Design Principles

**Single Responsibility** — Each mixin class has one clearly defined responsibility. Composition at the viewset or model level is explicit.

**No Magic** — `drf-commons` does not auto-discover, monkey-patch, or alter DRF's global behavior. All integration is opt-in.

**Async-First** — Context management uses `ContextVar`, not `threading.local()`. Middleware supports both WSGI and ASGI handlers.

**Database Efficiency** — Bulk operations default to `QuerySet.bulk_update()` and `QuerySet.bulk_create()`, avoiding O(n) query patterns.

**Fail Loudly** — `VersionConflictError`, `MiddlewareChecker.require()`, and configuration validators surface problems at startup or on first use rather than producing silent failures.

---

## Production Usage

### Middleware Validation

`drf-commons` validates its own middleware requirements at application startup. If `UserActionMixin` or `CurrentUserField` is used without `CurrentUserMiddleware`, the application raises `ImproperlyConfigured` at startup rather than failing silently at runtime.

### Configuring for Scale

```python
# settings.py
COMMON = {
    # Bulk operation chunk sizing
    'BULK_OPERATION_BATCH_SIZE': 2000,

    # Import processing chunk sizing
    'IMPORT_BATCH_SIZE': 500,

    # Query performance thresholds for alerting
    'DEBUG_SLOW_REQUEST_THRESHOLD': 0.5,      # seconds
    'DEBUG_HIGH_QUERY_COUNT_THRESHOLD': 20,   # query count
    'DEBUG_SLOW_QUERY_THRESHOLD': 0.05,       # seconds per query
}
```

### Soft Delete Integration

```python
class ArticleViewSet(BaseViewSet):
    queryset = Article.objects.filter(is_active=True)  # exclude soft-deleted

    def perform_destroy(self, instance):
        instance.soft_delete()  # non-destructive deletion
```

---

## Extensibility

Every component in `drf-commons` is a building block, not a ceiling.

### Custom ViewSet Composition

```python
from drf_commons.views.mixins import (
    ListModelMixin,
    RetrieveModelMixin,
    BulkCreateModelMixin,
    FileExportMixin,
)
from rest_framework.viewsets import GenericViewSet

class CustomViewSet(
    ListModelMixin,
    RetrieveModelMixin,
    BulkCreateModelMixin,
    FileExportMixin,
    GenericViewSet
):
    """Read-only viewset with bulk creation and export, no standard create."""
    pass
```

### Custom Response Format

```python
from drf_commons.response import success_response

def custom_response(data, message='', **meta):
    response = success_response(data=data, message=message)
    response.data['_meta'] = meta
    return response
```

### Extending `BaseModelSerializer`

```python
class AuditedSerializer(BaseModelSerializer):
    def create(self, validated_data):
        instance = super().create(validated_data)
        AuditLog.objects.create(
            action='CREATE',
            model=instance.__class__.__name__,
            object_id=instance.pk,
            user=get_current_user(),
        )
        return instance
```

---

## Performance Considerations

- **Bulk operations** bypass individual `save()` calls using `bulk_update()` and `bulk_create()`. For 1000-record updates, this reduces database round-trips from 1000 to 1.
- **ContextVar** user resolution eliminates per-request serializer context threading overhead.
- **`select_related` / `prefetch_related`** — `drf-commons` does not force queryset evaluation; queryset optimization remains your responsibility.
- **Chunk-based import** processes large files in configurable batches, bounding peak memory usage.
- **Lazy-loaded exporters** — Export and import dependencies (`openpyxl`, `pandas`, `weasyprint`) are imported only when the relevant service is invoked.

---

## Use Cases

**Multi-tenant SaaS APIs** — `UserActionMixin` + `CurrentUserMiddleware` provide consistent audit trails across all tenant operations without per-view instrumentation.

**High-volume data pipelines** — `BulkViewSet` + configurable batch sizes handle thousands of records per API call efficiently.

**Enterprise data management** — `FileImportService` supports multi-model imports with dependency ordering, foreign key resolution, and progress callbacks.

**Microservice backends** — Standardized response envelopes enable consistent API contracts across multiple service deployments.

**Internal tooling APIs** — Pre-composed viewsets reduce the time to a working, production-quality endpoint from hours to minutes.

---

## Engineering Capabilities Demonstrated

This library demonstrates the following backend engineering competencies:

**Framework Internals Mastery**
Deep understanding of DRF's serializer resolution pipeline, viewset mixin composition, and renderer/parser integration. Extends DRF at documented extension points rather than patching internals.

**Reusable Abstraction Design**
Consistent application of mixin-based composition. Every component is independently usable and composable without dependency on sibling components.

**Async-Safe Architecture**
Replacement of thread-local storage with `ContextVar` for proper ASGI compatibility — a non-trivial distinction with significant production implications.

**Production API Design**
Standardized response envelopes, audit trail automation, optimistic locking, and soft delete — patterns required in any production-grade API but absent from DRF defaults.

**Database Performance Engineering**
`bulk_update()` / `bulk_create()` integration with automatic audit field population. Query count monitoring and slow query detection built into the observability layer.

**Scalable Backend Development**
Chunk-based file processing, configurable batch sizes, and lazy dependency loading ensure the library operates predictably under production workloads.

**API Standardization**
Envelope-based responses, ISO8601 timestamps, and consistent error formats provide a contract-stable API surface for client consumers.

**Framework Extension Engineering**
Custom DRF serializer field architecture (`ConfigurableRelatedFieldMixin`) provides a clean extension point for the 20+ pre-built field variants. Adding new field types requires implementing a single abstract method.

---

## Contributing

Contributions are welcome. Please read the development documentation before submitting a pull request.

```bash
git clone https://github.com/htvictoire/drf-commons
cd drf-commons
pip install -e ".[export,import,debug]"
pip install -r docs/requirements.txt
make install-dev
make quality  # format + lint + type-check
make test
```

---

## License

MIT License. See [LICENSE](LICENSE) for full text.

---

*Built with precision for production Django REST Framework deployments.*

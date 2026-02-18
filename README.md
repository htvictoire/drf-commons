# drf-commons

Production-grade utilities that fix structural limitations in Django REST Framework.

## Why this exists

Django REST Framework is powerful, but large production APIs repeatedly hit the same friction points:

- repetitive serializer and view logic
- inconsistent error and success payload structures
- no shared response envelope contract across teams
- recurring boilerplate for bulk operations and import/export workflows
- ad-hoc observability patterns that drift over time

`drf-commons` addresses these with reusable abstractions that standardize behavior while staying compatible with DRF's architecture.

## Features

- composable CRUD and bulk view mixins for consistent endpoint behavior
- configurable related-field serializer system for complex relation IO contracts
- standardized API response helpers (`success_response`, `error_response`, `validation_error_response`)
- reusable base serializers with bulk-update support (`BaseModelSerializer`, `BulkUpdateListSerializer`)
- file import pipeline with validation, transforms, lookup resolution, and batch persistence
- file export pipeline for CSV/XLSX/PDF with configurable column metadata
- current-user context propagation for model-level actor attribution
- category-aware debug/logging utilities for production observability

## Installation

Base package:

```bash
pip install drf-commons
```

Optional extras:

```bash
# XLSX/PDF export
pip install drf-commons[export]

# file import pipeline
pip install drf-commons[import]
```

Configure Django:

```python
INSTALLED_APPS = [
    "drf_commons",
]
```

## Example

Before:

```python
from rest_framework import status, viewsets
from rest_framework.response import Response

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                "ok": True,
                "message": "Incident created",
                "result": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
```

After:

```python
from drf_commons.views.base import BaseViewSet

class IncidentViewSet(BaseViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    return_data_on_create = True

    def on_create_message(self):
        return "Incident created"

    # `create` is inherited and returns standardized envelope via success_response.
```

## Architecture

Simple model:

- **Presentation layer**: DRF view mixins and response helpers standardize endpoint contracts.
- **Serialization layer**: base serializers and configurable relation fields reduce repeated IO logic.
- **Domain model layer**: model mixins add reusable timestamp/user/soft-delete/version patterns.
- **Service layer**: import/export workflows handle file processing, validation, and persistence orchestration.
- **Observability layer**: debug middleware, decorators, and category-gated logging provide operational visibility.

The library ships as one Django app with composable modules.

## Production usage

Built for and used in real production systems where API consistency, maintainability, and operational control are mandatory.

## Documentation

- Full technical docs: `docs/`
- API reference is generated from source modules under `drf_commons`
- Local docs build:

```bash
make -C docs html
```

## Requirements

- Python >= 3.8
- Django >= 3.2
- djangorestframework >= 3.12

## License

MIT

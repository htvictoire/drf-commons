# DRF Commons

> **⚠️ UNDER DEVELOPMENT**: This library is currently under active development. APIs may change, and some features may not be fully stable yet.

A comprehensive collection of reusable Django REST Framework utilities and components designed to accelerate API development.

## Features

### Core Modules

- **Current User**: Middleware and utilities for accessing the current user context
- **Debug**: Advanced logging and debugging tools with categorized loggers
- **Decorators**: Performance monitoring, caching, database optimization, and logging decorators
- **Filters**: Enhanced filtering and ordering capabilities including computed fields
- **Middlewares**: Current user tracking and debug middleware
- **Models**: Base models, mixins, and custom fields for common patterns
- **Pagination**: Flexible pagination classes
- **Response**: Standardized API response utilities
- **Serializers**: Enhanced serializers with custom fields and mixins
- **Views**: ViewSet mixins for CRUD, bulk operations, and import/export

### Services

- **Export File**: Export data to CSV, XLSX, and PDF formats
- **Import from File**: Robust file import with validation and bulk operations

## Installation

Install the base package:

```bash
pip install drf-commons
```

Install with specific features:

```bash
# For export functionality (XLSX and PDF)
pip install drf-commons[export]

# For import functionality
pip install drf-commons[import]

# For dynamic configuration
pip install drf-commons[config]

# For all features
pip install drf-commons[all]

# For development
pip install drf-commons[dev,test]
```

## Quick Start

### 1. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ... your apps
    'drf_commons.current_user',
    'drf_commons.debug',
    'drf_commons.filters',
    'drf_commons.pagination',
    'drf_commons.response',
    'drf_commons.serializers',
    'drf_commons.views',
]
```

### 2. Add Middleware (Optional)

```python
MIDDLEWARE = [
    # ... other middleware
    'drf_commons.middlewares.current_user.CurrentUserMiddleware',
    'drf_commons.middlewares.debug.DebugMiddleware',
]
```

### 3. Use in Your Code

```python
from drf_commons.views.base import BaseViewSet
from drf_commons.serializers.base import BaseSerializer
from drf_commons.models.base import BaseModel
from drf_commons.pagination.base import CustomPageNumberPagination

class MyModel(BaseModel):
    # Your model fields
    pass

class MySerializer(BaseSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'

class MyViewSet(BaseViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MySerializer
    pagination_class = CustomPageNumberPagination
```

## Usage Examples

### Export Data

```python
from drf_commons.services import ExportService

service = ExportService()

# Export to CSV (no optional dependencies required)
response = service.export_csv(
    data_rows=data,
    includes=['id', 'name', 'created_at'],
    column_config={},
    filename='export.csv',
    export_headers=[],
    document_titles=[]
)

# Export to XLSX (requires openpyxl)
response = service.export_xlsx(...)

# Export to PDF (requires weasyprint)
response = service.export_pdf(...)
```

### Import Data

```python
from drf_commons.services import FileImportService

config = {
    'model': MyModel,
    'fields': {
        'name': {'required': True},
        'email': {'required': True, 'unique': True},
    }
}

service = FileImportService(config)
result = service.import_file(file_path)
```

### Use Decorators

```python
from drf_commons.decorators.performance import measure_performance
from drf_commons.decorators.cache import cached_method

class MyViewSet(BaseViewSet):
    @measure_performance
    @cached_method(timeout=300)
    def expensive_operation(self):
        # Your expensive operation
        pass
```

## Requirements

- Python >= 3.8
- Django >= 3.2
- djangorestframework >= 3.12

## Optional Dependencies

Different features require different dependencies:

### Core Package (No optional dependencies)

The base installation includes:

- Models, Serializers, Views, Pagination, Response utilities
- CSV export (no additional dependencies required)
- Filters, Decorators, Middleware

### File Export (`[export]`)

For XLSX and PDF export functionality:

- `openpyxl >= 3.0` - Excel (XLSX) export
- `weasyprint >= 60.0` - PDF export

### File Import (`[import]`)

For importing data from CSV and Excel files:

- `pandas >= 1.3` - Data processing and file parsing
- `openpyxl >= 3.0` - Excel file reading

### Dynamic Configuration (`[config]`)

For runtime configuration management:

- `django-constance >= 2.9` - Dynamic Django settings

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/drf-common.git
cd drf-common

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e .[dev,test,all]
```

### Run Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black .

# Sort imports
isort .

# Lint
flake8

# Type checking
mypy drf_commons
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Author

Victoire HABAMUNGU

## Support

For issues and questions, please use the GitHub issue tracker.

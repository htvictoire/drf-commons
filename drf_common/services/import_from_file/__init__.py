"""
File import service package for importing data from CSV/Excel files.

This package provides a modular file import system with support for:
- Multiple file formats (CSV, XLSX, XLS)
- Multi-model imports with relationships
- Field transformations and validations
- Bulk operations with error handling
"""

from .config.enums import FileFormat
from .core.exceptions import ImportErrorRow, ImportValidationError
from .service import FileImportService

__all__ = ["FileImportService", "ImportErrorRow", "ImportValidationError", "FileFormat"]

"""
Service layer providing export and import functionality.
"""

from .export_file import ExportService

__all__ = ["ExportService", "FileImportService"]


def __getattr__(name):
    """Lazy load services to handle optional dependencies."""
    if name == "FileImportService":
        from .import_from_file import FileImportService

        return FileImportService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

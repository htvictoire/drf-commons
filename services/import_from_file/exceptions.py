"""
Exception classes for file import operations.
"""

from typing import Optional


class ImportErrorRow(Exception):
    """Raised to annotate a single-row error during processing."""
    
    def __init__(self, message: str, row_number: Optional[int] = None, field_name: Optional[str] = None):
        self.row_number = row_number
        self.field_name = field_name
        super().__init__(message)


class ImportValidationError(Exception):
    """Raised when import configuration is invalid."""
    pass
"""
Enums and constants for file import operations.
"""

from enum import Enum


class FileFormat(Enum):
    """Supported file formats for import."""

    CSV = "csv"
    XLSX = "xlsx"
    XLS = "xls"

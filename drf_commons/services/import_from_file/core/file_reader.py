"""
File reading and parsing utilities for import operations.
"""

from typing import Any, Dict

try:
    import pandas as pd
except ImportError as e:
    raise ImportError(
        "File import service requires pandas. "
        "Install it with: pip install drf-commons[import]"
    ) from e

from ..config.enums import FileFormat
from .exceptions import ImportValidationError


class FileReader:
    """Handles reading and parsing of different file formats."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.file_format = FileFormat(config["file_format"].lower())

    def read_file(self, file_obj) -> pd.DataFrame:
        """Read file based on configured format."""
        if self.file_format == FileFormat.CSV:
            df = self._read_csv(file_obj)
        elif self.file_format == FileFormat.XLSX:
            df = self._read_excel(file_obj, engine="openpyxl")
        elif self.file_format == FileFormat.XLS:
            df = self._read_excel(file_obj, engine="xlrd")
        else:
            raise ImportValidationError(f"Unsupported file format: {self.file_format}")

        # Normalize header whitespace
        df.rename(
            columns=lambda c: c.strip() if isinstance(c, str) else c, inplace=True
        )
        return df

    def _read_csv(self, file_obj) -> pd.DataFrame:
        """Read CSV file with optional configuration."""
        csv_options = self.config.get("csv_options", {})
        delimiter = csv_options.get("delimiter", ",")
        encoding = csv_options.get("encoding", "utf-8")
        return pd.read_csv(file_obj, delimiter=delimiter, encoding=encoding)

    def _read_excel(self, file_obj, engine: str) -> pd.DataFrame:
        """Read Excel file with specified engine."""
        return pd.read_excel(
            file_obj, engine=engine, header=4
        )  # Header is on row 5 (0-indexed)

    def validate_headers(self, df_columns: list, required_columns: set) -> None:
        """Validate file headers against configuration."""
        file_columns = set(df_columns)

        # Check for missing columns
        missing_columns = required_columns - file_columns
        if missing_columns:
            sorted_missing = sorted(missing_columns)
            raise ImportValidationError(
                f"Missing columns from template: {sorted_missing}. "
                f"Please use the exact template provided for this import."
            )

        # Check for extra columns
        extra_columns = file_columns - required_columns
        if extra_columns:
            sorted_extra = sorted(extra_columns)
            raise ImportValidationError(
                f"Unexpected columns found: {sorted_extra}. "
                f"Please use only the columns defined in the template."
            )

"""
Export service for Django REST Framework viewsets.

Provides export functionality that works with the frontend export dialog.
"""

from typing import Any, Dict, List

from django.http import HttpResponse

from .data_processor import process_export_data
from .exporters import CSVExporter, PDFExporter, XLSXExporter


class ExportService:
    """
    Service that provides export functionality for different file formats.

    The frontend export dialog sends:
    - file_type: "pdf", "xlsx", or "csv"
    - includes: comma-separated list of field names to include
    - column_config: mapping of field names to display labels
    - data: optional pre-filtered data array
    """

    def __init__(self):
        self._exporters = {
            "csv": CSVExporter(),
            "xlsx": XLSXExporter(),
            "pdf": PDFExporter(),
        }

    def process_export_data(
        self,
        provided_data: List[Dict],
        includes: List[str],
        column_config: Dict[str, Dict],
        file_titles: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Process export data and prepare it for different formats.

        Args:
            provided_data: Raw data to export
            includes: List of field names to include
            column_config: Column configuration dict
            file_titles: Optional list of titles

        Returns:
            Dict containing processed data and metadata
        """
        return process_export_data(provided_data, includes, column_config, file_titles)

    def export_csv(
        self,
        data_rows: List[Dict],
        includes: List[str],
        column_config: Dict[str, Dict],
        filename: str,
        export_headers: List[str],
        document_titles: List[str],
    ) -> HttpResponse:
        """Export data as CSV file."""
        return self._exporters["csv"].export(
            data_rows,
            includes,
            column_config,
            filename,
            export_headers,
            document_titles,
        )

    def export_xlsx(
        self,
        data_rows: List[Dict],
        includes: List[str],
        column_config: Dict[str, Dict],
        filename: str,
        export_headers: List[str],
        document_titles: List[str],
    ) -> HttpResponse:
        """Export data as Excel file."""
        return self._exporters["xlsx"].export(
            data_rows,
            includes,
            column_config,
            filename,
            export_headers,
            document_titles,
        )

    def export_pdf(
        self,
        data_rows: List[Dict],
        includes: List[str],
        column_config: Dict[str, Dict],
        filename: str,
        export_headers: List[str],
        document_titles: List[str],
    ) -> HttpResponse:
        """Export data as PDF file."""
        return self._exporters["pdf"].export(
            data_rows,
            includes,
            column_config,
            filename,
            export_headers,
            document_titles,
        )

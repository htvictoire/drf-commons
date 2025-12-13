"""
Export service for Django REST Framework viewsets.

Provides export functionality that works with the frontend export dialog.
"""

from typing import Any, Dict, List

from django.http import HttpResponse

from .data_processor import process_export_data


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
        self._exporters = {}

    def _get_exporter(self, format_type: str):
        """
        Lazy load and cache exporter for the given format.

        Args:
            format_type: Export format ("csv", "xlsx", or "pdf")

        Returns:
            Exporter instance for the specified format
        """
        if format_type not in self._exporters:
            if format_type == "csv":
                from .exporters.csv_exporter import CSVExporter
                self._exporters["csv"] = CSVExporter()
            elif format_type == "xlsx":
                from .exporters.xlsx_exporter import XLSXExporter
                self._exporters["xlsx"] = XLSXExporter()
            elif format_type == "pdf":
                from .exporters.pdf_exporter import PDFExporter
                self._exporters["pdf"] = PDFExporter()
            else:
                raise ValueError(f"Unsupported export format: {format_type}")

        return self._exporters[format_type]

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
        exporter = self._get_exporter("csv")
        return exporter.export(
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
        exporter = self._get_exporter("xlsx")
        return exporter.export(
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
        exporter = self._get_exporter("pdf")
        return exporter.export(
            data_rows,
            includes,
            column_config,
            filename,
            export_headers,
            document_titles,
        )

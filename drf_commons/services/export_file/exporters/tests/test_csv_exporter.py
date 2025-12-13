"""
Tests for CSV export functionality.

Tests CSV exporter functionality for exporting data to CSV format.
"""

from django.http import HttpResponse

from drf_commons.common_tests.base_cases import DrfCommonTestCase

from ..csv_exporter import CSVExporter


class CSVExporterTests(DrfCommonTestCase):
    """Tests for CSVExporter."""

    def setUp(self):
        super().setUp()
        self.exporter = CSVExporter()
        self.sample_data = [
            {"id": 1, "name": "John Doe", "email": "john@example.com"},
            {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
        ]
        self.includes = ["id", "name", "email"]
        self.column_config = {
            "id": {"label": "ID"},
            "name": {"label": "Name"},
            "email": {"label": "Email"},
        }
        self.filename = "test_export.csv"
        self.export_headers = ["Test Export Report"]
        self.document_titles = ["User Data Export"]

    def test_export_returns_http_response(self):
        """Test export returns HttpResponse."""
        response = self.exporter.export(
            self.sample_data,
            self.includes,
            self.column_config,
            self.filename,
            self.export_headers,
            self.document_titles,
        )

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(self.filename, response["Content-Disposition"])

    def test_export_with_empty_data(self):
        """Test export with empty data returns response."""
        response = self.exporter.export(
            [],
            self.includes,
            self.column_config,
            self.filename,
            self.export_headers,
            self.document_titles,
        )

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_export_content_type(self):
        """Test export sets correct content type."""
        response = self.exporter.export(
            self.sample_data,
            self.includes,
            self.column_config,
            self.filename,
            self.export_headers,
            self.document_titles,
        )

        self.assertEqual(response["Content-Type"], "text/csv")

    def test_export_filename_header(self):
        """Test export sets correct filename in headers."""
        response = self.exporter.export(
            self.sample_data,
            self.includes,
            self.column_config,
            self.filename,
            self.export_headers,
            self.document_titles,
        )

        content_disposition = response["Content-Disposition"]
        self.assertIn("attachment", content_disposition)
        self.assertIn(self.filename, content_disposition)

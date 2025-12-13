"""
Tests for Excel export functionality.

Tests Excel exporter functionality for exporting data to XLSX format.
"""

from django.http import HttpResponse

from drf_common.common_tests.base_cases import DrfCommonTestCase

from ..xlsx_exporter import XLSXExporter


class XLSXExporterTests(DrfCommonTestCase):
    """Tests for XLSXExporter."""

    def setUp(self):
        super().setUp()
        self.exporter = XLSXExporter()
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
        self.filename = "test_export.xlsx"
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
        expected_content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        self.assertEqual(response["Content-Type"], expected_content_type)
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
        expected_content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        self.assertEqual(response["Content-Type"], expected_content_type)

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

        expected_content_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        self.assertEqual(response["Content-Type"], expected_content_type)

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

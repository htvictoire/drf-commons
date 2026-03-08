"""
Tests for ExportService class.

Tests main service functionality for exporting data to different formats.
"""

from django.http import HttpResponse

from drf_commons.common_tests.base_cases import DrfCommonTestCase

from ..service import ExportService


class ExportServiceTests(DrfCommonTestCase):
    """Tests for ExportService."""

    def setUp(self):
        super().setUp()
        self.service = ExportService()
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
        self.filename = "test_export"
        self.export_headers = ["ID", "Name", "Email"]
        self.document_titles = ["Test Export"]

    def test_service_initialization(self):
        """Test service initializes with correct exporters."""
        self.assertEqual(self.service._exporters, {})

    def test_process_export_data(self):
        """Test data processing functionality."""
        result = self.service.process_export_data(
            self.sample_data, self.includes, self.column_config
        )
        self.assertIsInstance(result, dict)

    def test_export_csv_returns_http_response(self):
        """Test CSV export returns HttpResponse."""
        response = self.service.export_csv(
            self.sample_data,
            self.includes,
            self.column_config,
            self.filename,
            self.export_headers,
            self.document_titles,
        )
        self.assertIsInstance(response, HttpResponse)

    def test_export_xlsx_returns_http_response(self):
        """Test Excel export returns HttpResponse."""
        response = self.service.export_xlsx(
            self.sample_data,
            self.includes,
            self.column_config,
            self.filename,
            self.export_headers,
            self.document_titles,
        )
        self.assertIsInstance(response, HttpResponse)

    def test_export_pdf_returns_http_response(self):
        """Test PDF export returns HttpResponse."""
        response = self.service.export_pdf(
            self.sample_data,
            self.includes,
            self.column_config,
            self.filename,
            self.export_headers,
            self.document_titles,
        )
        self.assertIsInstance(response, HttpResponse)

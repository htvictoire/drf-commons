"""
Tests for data processing functions.

Tests data processing functionality used in export operations.
"""

from drf_common.common_tests.base_cases import DrfCommonTestCase

from ..data_processor import process_export_data


class DataProcessorTests(DrfCommonTestCase):
    """Tests for data processing functions."""

    def setUp(self):
        super().setUp()
        self.sample_data = [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "status": "active",
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "status": "inactive",
            },
        ]

    def test_process_export_data_with_includes(self):
        """Test data processing with specific includes."""
        includes = ["id", "name"]
        column_config = {"id": {"label": "ID"}, "name": {"label": "Name"}}

        result = process_export_data(self.sample_data, includes, column_config)

        self.assertIsInstance(result, dict)
        self.assertIn("table_data", result)
        self.assertIn("remaining_includes", result)
        self.assertIn("export_headers", result)
        self.assertIn("document_titles", result)

    def test_process_export_data_with_column_config(self):
        """Test data processing with column configuration."""
        includes = ["id", "name", "email"]
        column_config = {
            "id": {"label": "ID"},
            "name": {"label": "Full Name"},
            "email": {"label": "Email Address"},
        }

        result = process_export_data(self.sample_data, includes, column_config)

        self.assertIsInstance(result, dict)

    def test_process_export_data_with_titles(self):
        """Test data processing with document titles."""
        includes = ["id", "name"]
        column_config = {"id": {"label": "ID"}, "name": {"label": "Name"}}
        file_titles = ["User Export Report"]

        result = process_export_data(
            self.sample_data, includes, column_config, file_titles
        )

        self.assertIsInstance(result, dict)

    def test_process_export_data_empty_data(self):
        """Test data processing with empty data."""
        includes = ["id", "name"]
        column_config = {"id": {"label": "ID"}, "name": {"label": "Name"}}

        result = process_export_data([], includes, column_config)

        self.assertIsInstance(result, dict)

"""
Tests for FileExportMixin.
"""

from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth import get_user_model
from django.http import HttpResponse

from drf_commons.common_tests.base_cases import ViewTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.views.mixins.import_export import FileExportMixin

User = get_user_model()


def _request(data=None):
    req = Mock()
    req.data = data or {}
    return req


def _export_request(file_type="csv", includes=None, data=None):
    return _request({
        "file_type": file_type,
        "includes": includes or ["id", "name"],
        "column_config": {},
        "data": data or [{"id": 1, "name": "test"}],
        "file_titles": [],
    })


class FileExportMixinTests(ViewTestCase):
    """Tests for FileExportMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_file_export_mixin_has_export_method(self):
        mixin = FileExportMixin()
        self.assertTrue(hasattr(mixin, "export_data"))

    def test_file_export_mixin_export_method_is_action(self):
        mixin = FileExportMixin()
        self.assertTrue(hasattr(mixin.export_data, "mapping"))

    def test_invalid_file_type_returns_400(self):
        response = FileExportMixin().export_data(_export_request(file_type="doc"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("file_type", response.data["errors"])

    def test_no_data_provided_returns_400(self):
        response = FileExportMixin().export_data(
            _request({"file_type": "csv", "includes": ["id"], "column_config": {}, "data": None, "file_titles": []})
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("data", response.data["errors"])

    def test_invalid_includes_type_returns_400(self):
        response = FileExportMixin().export_data(
            _request({"file_type": "csv", "includes": 123, "column_config": {}, "data": [{"id": 1}], "file_titles": []})
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("includes", response.data["errors"])

    def test_empty_includes_returns_400(self):
        response = FileExportMixin().export_data(
            _request({"file_type": "csv", "includes": [], "column_config": {}, "data": [{"id": 1}], "file_titles": []})
        )
        self.assertEqual(response.status_code, 400)

    @patch("drf_commons.views.mixins.import_export.ExportService")
    def test_csv_export_returns_file_response(self, mock_svc):
        mock_svc.return_value.process_export_data.return_value = {
            "table_data": [], "remaining_includes": ["id"], "export_headers": {}, "document_titles": []
        }
        mock_svc.return_value.export_csv.return_value = HttpResponse(b"csv", content_type="text/csv")
        response = FileExportMixin().export_data(_export_request(file_type="csv"))
        self.assertEqual(response.status_code, 200)
        mock_svc.return_value.export_csv.assert_called_once()

    @patch("drf_commons.views.mixins.import_export.ExportService")
    def test_xlsx_export_returns_file_response(self, mock_svc):
        mock_svc.return_value.process_export_data.return_value = {
            "table_data": [], "remaining_includes": ["id"], "export_headers": {}, "document_titles": []
        }
        mock_svc.return_value.export_xlsx.return_value = HttpResponse(b"xlsx", content_type="application/vnd.ms-excel")
        response = FileExportMixin().export_data(_export_request(file_type="xlsx"))
        self.assertEqual(response.status_code, 200)
        mock_svc.return_value.export_xlsx.assert_called_once()

    @patch("drf_commons.views.mixins.import_export.ExportService")
    def test_pdf_export_returns_file_response(self, mock_svc):
        mock_svc.return_value.process_export_data.return_value = {
            "table_data": [], "remaining_includes": ["id"], "export_headers": {}, "document_titles": []
        }
        mock_svc.return_value.export_pdf.return_value = HttpResponse(b"pdf", content_type="application/pdf")
        response = FileExportMixin().export_data(_export_request(file_type="pdf"))
        self.assertEqual(response.status_code, 200)
        mock_svc.return_value.export_pdf.assert_called_once()

    @patch("drf_commons.views.mixins.import_export.logger")
    @patch("drf_commons.views.mixins.import_export.ExportService")
    def test_export_data_sanitizes_unexpected_exception(self, mock_export_service, mock_logger):
        """Unexpected export exceptions should not leak internal details."""
        mock_export_service.return_value.process_export_data.side_effect = RuntimeError(
            "database connection failed: secret://internal"
        )
        mixin = FileExportMixin()
        request = Mock()
        request.data = {
            "file_type": "csv",
            "includes": ["id"],
            "column_config": {},
            "data": [{"id": 1}],
            "file_titles": [],
        }

        response = mixin.export_data(request)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.data["message"], "Data export failed")
        self.assertIn("error_id", response.data["data"])
        self.assertIn("export", response.data["errors"])
        self.assertNotIn("database connection failed", str(response.data))
        self.assertNotIn("secret://internal", str(response.data))
        mock_logger.exception.assert_called_once()


class NormalizeIncludesTests(ViewTestCase):
    """Tests for FileExportMixin._normalize_includes()."""

    def test_comma_separated_string_is_split_into_list(self):
        result = FileExportMixin._normalize_includes("id,name,email")
        self.assertEqual(result, ["id", "name", "email"])

    def test_list_input_is_returned_deduplicated(self):
        result = FileExportMixin._normalize_includes(["id", "name", "id"])
        self.assertEqual(result, ["id", "name"])

    def test_empty_strings_are_skipped(self):
        result = FileExportMixin._normalize_includes(["id", "", "  ", "name"])
        self.assertEqual(result, ["id", "name"])

    def test_non_string_item_in_list_raises_type_error(self):
        with self.assertRaises(TypeError):
            FileExportMixin._normalize_includes(["id", 42])

    def test_non_list_non_string_input_raises_type_error(self):
        with self.assertRaises(TypeError):
            FileExportMixin._normalize_includes(123)

    def test_all_empty_fields_raises_value_error(self):
        with self.assertRaises(ValueError):
            FileExportMixin._normalize_includes(["", "  "])

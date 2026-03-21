"""
Tests for FileImportMixin.
"""

from unittest.mock import MagicMock, Mock, mock_open, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from drf_commons.common_tests.base_cases import ViewTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.services.import_from_file import ImportValidationError
from drf_commons.views.mixins.import_export import FileImportMixin

User = get_user_model()


class _Fixture(FileImportMixin):
    """Minimal concrete subclass for testing."""

    import_file_config = {"order": ["Item"], "models": {"Item": {}}}
    import_template_name = "items_template.xlsx"

    def get_queryset(self):
        qs = MagicMock()
        qs.delete.return_value = (3, {"Item": 3})
        return qs


def _request(files=None, data=None, path="/api/items/import-from-file/"):
    req = Mock()
    req.FILES = files if files is not None else {}
    req.data = data if data is not None else {}
    req.path = path
    req.build_absolute_uri.return_value = (
        "http://testserver/api/items/download-import-template/"
    )
    return req


def _result(created=5, updated=0, failed=0, rows=None):
    return {
        "summary": {"created": created, "updated": updated, "failed": failed},
        "rows": rows or [],
    }


class FileImportMixinTests(ViewTestCase):
    """Tests for FileImportMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_file_import_mixin_has_import_method(self):
        mixin = FileImportMixin()
        self.assertTrue(hasattr(mixin, "import_file"))

    def test_file_import_mixin_has_download_template_method(self):
        mixin = FileImportMixin()
        self.assertTrue(hasattr(mixin, "download_import_template"))

    def test_file_import_mixin_has_required_attributes(self):
        mixin = FileImportMixin()
        self.assertTrue(hasattr(mixin, "import_file_config"))
        self.assertTrue(hasattr(mixin, "import_template_name"))
        self.assertTrue(hasattr(mixin, "import_transforms"))
        self.assertIsNone(mixin.import_transforms)

    def test_get_import_transforms_returns_isolated_dict(self):
        """Resolved transforms should not share mutable class state."""

        class DummyImportMixin(FileImportMixin):
            import_transforms = {"normalize": lambda v: v}

        mixin = DummyImportMixin()
        transforms = mixin.get_import_transforms()
        transforms["new_key"] = lambda v: v

        self.assertIn("normalize", DummyImportMixin.import_transforms)
        self.assertNotIn("new_key", DummyImportMixin.import_transforms)

    def test_parse_bool_accepts_native_bool_and_int_values(self):
        self.assertTrue(FileImportMixin.parse_bool(True, "append_data"))
        self.assertFalse(FileImportMixin.parse_bool(False, "append_data"))
        self.assertTrue(FileImportMixin.parse_bool(1, "append_data"))
        self.assertFalse(FileImportMixin.parse_bool(0, "append_data"))

    def test_parse_bool_accepts_string_values(self):
        self.assertTrue(FileImportMixin.parse_bool("true", "append_data"))
        self.assertTrue(FileImportMixin.parse_bool("YES", "append_data"))
        self.assertTrue(FileImportMixin.parse_bool("on", "append_data"))
        self.assertFalse(FileImportMixin.parse_bool("false", "append_data"))
        self.assertFalse(FileImportMixin.parse_bool("No", "append_data"))
        self.assertFalse(FileImportMixin.parse_bool("", "append_data"))

    def test_parse_bool_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            FileImportMixin.parse_bool("maybe", "append_data")
        with self.assertRaises(ValueError):
            FileImportMixin.parse_bool(2, "append_data")


class FileImportMixinImportFileTests(ViewTestCase):
    """Tests for FileImportMixin.import_file() branches."""

    def test_no_file_returns_400(self):
        response = _Fixture().import_file(_request(files={}, data={"append_data": "true"}))
        self.assertEqual(response.status_code, 400)
        self.assertIn("file", response.data["errors"])

    def test_invalid_flag_value_returns_400(self):
        uploaded = SimpleUploadedFile("data.csv", b"col\nval")
        response = _Fixture().import_file(
            _request(files={"file": uploaded}, data={"append_data": "maybe"})
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("mode", response.data["errors"])

    def test_neither_flag_set_returns_400(self):
        uploaded = SimpleUploadedFile("data.csv", b"col\nval")
        response = _Fixture().import_file(_request(files={"file": uploaded}, data={}))
        self.assertEqual(response.status_code, 400)

    def test_both_flags_true_returns_400(self):
        uploaded = SimpleUploadedFile("data.csv", b"col\nval")
        response = _Fixture().import_file(
            _request(files={"file": uploaded}, data={"append_data": "true", "replace_data": "true"})
        )
        self.assertEqual(response.status_code, 400)

    @patch("drf_commons.services.import_from_file.FileImportService")
    @patch("drf_commons.views.mixins.import_export.transaction")
    def test_replace_data_all_success_returns_201(self, mock_txn, mock_service):
        mock_service.return_value.import_file.return_value = _result()
        uploaded = SimpleUploadedFile("data.csv", b"col\nval")
        response = _Fixture().import_file(
            _request(files={"file": uploaded}, data={"replace_data": "true"})
        )
        self.assertEqual(response.status_code, 201)

    @patch("drf_commons.services.import_from_file.FileImportService")
    @patch("drf_commons.views.mixins.import_export.transaction")
    def test_replace_data_with_failures_rolls_back_and_returns_422(self, mock_txn, mock_service):
        failed_rows = [{"status": "failed", "row": 1, "error": "bad value"}]
        mock_service.return_value.import_file.return_value = _result(
            created=2, failed=1, rows=failed_rows
        )
        uploaded = SimpleUploadedFile("data.csv", b"col\nval")
        response = _Fixture().import_file(
            _request(files={"file": uploaded}, data={"replace_data": "true"})
        )
        self.assertEqual(response.status_code, 422)
        mock_txn.set_rollback.assert_called_once_with(True)

    @patch("drf_commons.services.import_from_file.FileImportService")
    def test_append_data_all_success_returns_201(self, mock_service):
        mock_service.return_value.import_file.return_value = _result()
        uploaded = SimpleUploadedFile("data.csv", b"col\nval")
        response = _Fixture().import_file(
            _request(files={"file": uploaded}, data={"append_data": "true"})
        )
        self.assertEqual(response.status_code, 201)

    @patch("drf_commons.services.import_from_file.FileImportService")
    def test_append_data_partial_failures_returns_207(self, mock_service):
        failed_rows = [{"status": "failed", "row": i, "error": "err"} for i in range(2)]
        mock_service.return_value.import_file.return_value = _result(
            created=3, failed=2, rows=failed_rows
        )
        uploaded = SimpleUploadedFile("data.csv", b"col\nval")
        response = _Fixture().import_file(
            _request(files={"file": uploaded}, data={"append_data": "true"})
        )
        self.assertEqual(response.status_code, 207)

    @patch("drf_commons.services.import_from_file.FileImportService")
    def test_append_data_all_failures_returns_422(self, mock_service):
        failed_rows = [{"status": "failed", "row": i, "error": "err"} for i in range(3)]
        mock_service.return_value.import_file.return_value = _result(
            created=0, failed=3, rows=failed_rows
        )
        uploaded = SimpleUploadedFile("data.csv", b"col\nval")
        response = _Fixture().import_file(
            _request(files={"file": uploaded}, data={"append_data": "true"})
        )
        self.assertEqual(response.status_code, 422)

    @patch("drf_commons.services.import_from_file.FileImportService")
    def test_validation_error_with_columns_includes_template_url(self, mock_service):
        mock_service.return_value.import_file.side_effect = ImportValidationError(
            "Missing required columns: name, age"
        )
        uploaded = SimpleUploadedFile("data.csv", b"col\nval")
        response = _Fixture().import_file(
            _request(files={"file": uploaded}, data={"append_data": "true"})
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("template_download_url", response.data["data"])

    @patch("drf_commons.services.import_from_file.FileImportService")
    def test_validation_error_without_columns_returns_generic_422(self, mock_service):
        mock_service.return_value.import_file.side_effect = ImportValidationError(
            "Transform function not found"
        )
        uploaded = SimpleUploadedFile("data.csv", b"col\nval")
        response = _Fixture().import_file(
            _request(files={"file": uploaded}, data={"append_data": "true"})
        )
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("template_download_url", response.data.get("data", {}))


class FileImportMixinDownloadTemplateTests(ViewTestCase):
    """Tests for FileImportMixin.download_import_template() branches."""

    def test_missing_template_returns_404_with_hint(self):
        mixin = _Fixture()
        with patch("drf_commons.views.mixins.import_export.os.path.exists", return_value=False):
            with patch.object(mixin, "_resolve_template_viewset_path", side_effect=Exception):
                response = mixin.download_import_template(Mock())
        self.assertEqual(response.status_code, 404)
        self.assertIn("template", response.data["errors"])

    def test_existing_template_returns_200_with_file_content(self):
        file_content = b"xlsx binary content"
        with patch("drf_commons.views.mixins.import_export.os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=file_content)):
                response = _Fixture().download_import_template(Mock())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, file_content)

    def test_ioerror_reading_template_returns_500(self):
        with patch("drf_commons.views.mixins.import_export.os.path.exists", return_value=True):
            with patch("builtins.open", side_effect=IOError("disk error")):
                response = _Fixture().download_import_template(Mock())
        self.assertEqual(response.status_code, 500)

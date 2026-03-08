"""
Tests for file import/export mixins.

Tests file import and export mixins functionality.
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model

from drf_commons.common_tests.base_cases import ViewTestCase
from drf_commons.common_tests.factories import UserFactory

from ..import_export import (
    FileExportMixin,
    FileImportMixin,
)

User = get_user_model()


class FileImportMixinTests(ViewTestCase):
    """Tests for FileImportMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_file_import_mixin_has_import_method(self):
        """Test FileImportMixin has import_file method."""
        mixin = FileImportMixin()
        self.assertTrue(hasattr(mixin, "import_file"))

    def test_file_import_mixin_has_download_template_method(self):
        """Test FileImportMixin has download_import_template method."""
        mixin = FileImportMixin()
        self.assertTrue(hasattr(mixin, "download_import_template"))

    def test_file_import_mixin_has_required_attributes(self):
        """Test FileImportMixin has required attributes."""
        mixin = FileImportMixin()
        self.assertTrue(hasattr(mixin, "import_file_config"))
        self.assertTrue(hasattr(mixin, "import_template_name"))
        self.assertTrue(hasattr(mixin, "import_transforms"))
        self.assertIsNone(mixin.import_transforms)

    def test_get_import_transforms_returns_isolated_dict(self):
        """Resolved import transforms should not share mutable class state."""

        class DummyImportMixin(FileImportMixin):
            import_transforms = {"normalize": lambda v: v}

        mixin = DummyImportMixin()
        transforms = mixin.get_import_transforms()
        transforms["new_key"] = lambda v: v

        self.assertIn("normalize", DummyImportMixin.import_transforms)
        self.assertNotIn("new_key", DummyImportMixin.import_transforms)

    def test_parse_bool_accepts_native_bool_and_int_values(self):
        """parse_bool should accept bool and integer representations."""
        self.assertTrue(FileImportMixin.parse_bool(True, "append_data"))
        self.assertFalse(FileImportMixin.parse_bool(False, "append_data"))
        self.assertTrue(FileImportMixin.parse_bool(1, "append_data"))
        self.assertFalse(FileImportMixin.parse_bool(0, "append_data"))

    def test_parse_bool_accepts_string_values(self):
        """parse_bool should accept common string representations."""
        self.assertTrue(FileImportMixin.parse_bool("true", "append_data"))
        self.assertTrue(FileImportMixin.parse_bool("YES", "append_data"))
        self.assertTrue(FileImportMixin.parse_bool("on", "append_data"))
        self.assertFalse(FileImportMixin.parse_bool("false", "append_data"))
        self.assertFalse(FileImportMixin.parse_bool("No", "append_data"))
        self.assertFalse(FileImportMixin.parse_bool("", "append_data"))

    def test_parse_bool_rejects_invalid_values(self):
        """parse_bool should reject unknown values with field-specific error."""
        with self.assertRaises(ValueError):
            FileImportMixin.parse_bool("maybe", "append_data")
        with self.assertRaises(ValueError):
            FileImportMixin.parse_bool(2, "append_data")


class FileExportMixinTests(ViewTestCase):
    """Tests for FileExportMixin."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.authenticate(self.user)

    def test_file_export_mixin_has_export_method(self):
        """Test FileExportMixin has export_data method."""
        mixin = FileExportMixin()
        self.assertTrue(hasattr(mixin, "export_data"))

    def test_file_export_mixin_export_method_is_action(self):
        """Test FileExportMixin export_data is an action."""
        mixin = FileExportMixin()
        self.assertTrue(hasattr(mixin, "export_data"))
        # Check that export_data is decorated as an action
        self.assertTrue(hasattr(mixin.export_data, "mapping"))

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

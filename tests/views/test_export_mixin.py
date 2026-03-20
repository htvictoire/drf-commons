"""
Tests for FileExportMixin.
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model

from drf_commons.common_tests.base_cases import ViewTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.views.mixins.import_export import FileExportMixin

User = get_user_model()


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

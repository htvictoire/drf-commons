"""
Tests for file import/export mixins.

Tests file import and export mixins functionality.
"""

from django.contrib.auth import get_user_model

from drf_common.common_tests.base_cases import ViewTestCase
from drf_common.common_tests.factories import UserFactory

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

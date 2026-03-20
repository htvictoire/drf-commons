"""
Tests for FileImportMixin.
"""

from unittest.mock import Mock

from django.contrib.auth import get_user_model

from drf_commons.common_tests.base_cases import ViewTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.views.mixins.import_export import FileImportMixin

User = get_user_model()


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

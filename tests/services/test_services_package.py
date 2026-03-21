"""
Tests for drf_commons.services lazy-loading mechanism.
"""

import drf_commons.services as services_module

from drf_commons.common_tests.base_cases import DrfCommonTestCase


class ServicesPackageTests(DrfCommonTestCase):
    """Tests for the services package __getattr__ lazy loader."""

    def test_file_import_service_lazy_loads(self):
        """FileImportService is importable via the services package."""
        from drf_commons.services import FileImportService
        from drf_commons.services.import_from_file import FileImportService as Direct

        self.assertIs(FileImportService, Direct)

    def test_getattr_unknown_name_raises_attribute_error(self):
        """Requesting an unknown attribute raises AttributeError."""
        with self.assertRaises(AttributeError):
            _ = services_module.NonExistentService

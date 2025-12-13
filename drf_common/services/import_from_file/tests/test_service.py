"""
Tests for FileImportService class.

Tests main service functionality for importing data from files.
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model

from drf_common.common_tests.base_cases import DrfCommonTestCase
from drf_common.common_tests.factories import UserFactory
from drf_common.common_conf import settings

from ..service import FileImportService

User = get_user_model()


class FileImportServiceTests(DrfCommonTestCase):
    """Tests for FileImportService."""

    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        self.sample_config = {
            "file_format": "xlsx",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "unique_by": [],
                    "update_if_exists": False,
                    "direct_columns": ["username", "email"],
                }
            },
        }

    def test_service_initialization(self):
        """Test service initializes with config."""
        service = FileImportService(self.sample_config)
        self.assertEqual(service.config, self.sample_config)
        self.assertEqual(service.batch_size, settings.IMPORT_BATCH_SIZE)
        self.assertEqual(service.transforms, {})

    def test_service_initialization_with_custom_batch_size(self):
        """Test service initialization with custom batch size."""
        service = FileImportService(self.sample_config, batch_size=100)
        self.assertEqual(service.batch_size, 100)

    def test_service_initialization_with_transforms(self):
        """Test service initialization with transform functions."""
        transforms = {"test_field": lambda x: x.upper()}
        service = FileImportService(self.sample_config, transforms=transforms)
        self.assertEqual(service.transforms, transforms)

    def test_service_initialization_with_progress_callback(self):
        """Test service initialization with progress callback."""
        callback = Mock()
        service = FileImportService(self.sample_config, progress_callback=callback)
        self.assertEqual(service.progress_callback, callback)

    def test_create_simple_config_static_method(self):
        """Test create_simple_config static method is accessible."""
        config = FileImportService.create_simple_config(
            "auth.User", ["username", "email"]
        )
        self.assertIn("file_format", config)
        self.assertIn("order", config)
        self.assertIn("models", config)
        self.assertEqual(config["models"]["main"]["model"], "auth.User")

    def test_validate_transforms_static_method(self):
        """Test validate_transforms static method is accessible."""
        # This should return empty list for valid config with no required transforms
        result = FileImportService.validate_transforms(self.sample_config, {})
        self.assertEqual(result, [])

    @patch("services.import_from_file.service.ConfigValidator")
    def test_validator_initialization(self, mock_validator):
        """Test validator is initialized with config and transforms."""
        transforms = {"test_field": lambda x: x}
        FileImportService(self.sample_config, transforms=transforms)

        mock_validator.assert_called_once_with(self.sample_config, transforms)

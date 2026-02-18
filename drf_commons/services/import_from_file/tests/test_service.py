"""
Tests for FileImportService class.

Tests main service functionality for importing data from files.
"""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
import pandas as pd

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.common_tests.factories import UserFactory
from drf_commons.common_conf import settings

from ..core.exceptions import ImportErrorRow
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

    @patch("drf_commons.services.import_from_file.service.ConfigValidator")
    def test_validator_initialization(self, mock_validator):
        """Test validator is initialized with config and transforms."""
        transforms = {"test_field": lambda x: x}
        FileImportService(self.sample_config, transforms=transforms)

        mock_validator.assert_called_once_with(self.sample_config, transforms)

    def test_import_chunk_preserves_failed_status_across_later_steps(self):
        """A row marked failed in one step must remain failed in later steps."""
        service = FileImportService.__new__(FileImportService)
        service.config = {
            "order": ["step1", "step2"],
            "models": {
                "step1": {
                    "model": "auth.User",
                    "step_name": "step1",
                    "unique_by": [],
                    "update_if_exists": False,
                },
                "step2": {
                    "model": "auth.User",
                    "step_name": "step2",
                    "unique_by": [],
                    "update_if_exists": False,
                },
            },
        }

        service.validator = Mock()
        service.validator.get_all_columns.return_value = ["username", "email"]
        service.file_reader = Mock()
        service.data_processor = Mock()
        service.bulk_ops = Mock()

        service.data_processor.collect_lookup_values.return_value = {}
        service.data_processor.prefetch_lookups.return_value = {}
        service.data_processor.prefetch_existing_objects.return_value = {}

        def prepare_kwargs(_row, model_config, _created, _lookups):
            if model_config["step_name"] == "step1":
                raise ImportErrorRow("username is required", field_name="username")
            return {"username": "should_not_apply", "email": "skip@test.com"}

        service.data_processor.prepare_kwargs_for_row.side_effect = prepare_kwargs

        service.bulk_ops.bulk_create_instances.return_value = {}
        service.bulk_ops.individual_create_instances.return_value = {}
        service.bulk_ops.bulk_update_instances.return_value = {}

        df = pd.DataFrame([{"username": "", "email": "invalid@test.com"}])

        result = service._import_chunk(df, start_row_offset=0, callback=None, total_file_rows=1)
        row = result["rows"][0]

        self.assertEqual(row["status"], "failed")
        self.assertGreater(len(row["errors"]), 0)
        self.assertEqual(result["summary"]["failed"], 1)
        self.assertEqual(result["summary"]["created"], 0)
        self.assertEqual(result["summary"]["updated"], 0)

    def test_import_chunk_marks_row_failed_when_update_persistence_fails(self):
        """Update persistence errors must be reflected in row status and summary."""
        service = FileImportService.__new__(FileImportService)
        service.config = {
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "unique_by": ["username"],
                    "update_if_exists": True,
                }
            },
        }

        existing = User.objects.create(username="existing_for_update", email="old@test.com")

        service.validator = Mock()
        service.validator.get_all_columns.return_value = ["username", "email"]
        service.file_reader = Mock()
        service.data_processor = Mock()
        service.bulk_ops = Mock()

        service.data_processor.collect_lookup_values.return_value = {}
        service.data_processor.prefetch_lookups.return_value = {}
        service.data_processor.prefetch_existing_objects.return_value = {
            ("existing_for_update",): existing
        }
        service.data_processor.prepare_kwargs_for_row.return_value = {
            "username": "existing_for_update",
            "email": "new@test.com",
        }
        service.data_processor.get_unique_key.return_value = ("existing_for_update",)

        service.bulk_ops.bulk_create_instances.return_value = {}
        service.bulk_ops.individual_create_instances.return_value = {}
        service.bulk_ops.bulk_update_instances.return_value = {0: "write failed"}

        df = pd.DataFrame([{"username": "existing_for_update", "email": "new@test.com"}])

        result = service._import_chunk(df, start_row_offset=0, callback=None, total_file_rows=1)
        row = result["rows"][0]

        self.assertEqual(row["status"], "failed")
        self.assertGreater(len(row["errors"]), 0)
        self.assertIn("write failed", row["errors"][0])
        self.assertEqual(result["summary"]["failed"], 1)
        self.assertEqual(result["summary"]["updated"], 0)

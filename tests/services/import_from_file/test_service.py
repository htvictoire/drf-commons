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

from drf_commons.services.import_from_file.core.exceptions import ImportErrorRow
from drf_commons.services.import_from_file.service import FileImportService

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

    def _make_stubbed_service(self, config=None):
        service = FileImportService.__new__(FileImportService)
        service.config = config or self.sample_config
        service.progress_callback = None
        service.validator = Mock()
        service.file_reader = Mock()
        service.data_processor = Mock()
        service.bulk_ops = Mock()
        service.validator.get_all_columns.return_value = ["username", "email"]
        service.data_processor.collect_lookup_values.return_value = {}
        service.data_processor.prefetch_lookups.return_value = {}
        service.data_processor.prefetch_existing_objects.return_value = {}
        service.bulk_ops.bulk_create_instances.return_value = {}
        service.bulk_ops.individual_create_instances.return_value = {}
        service.bulk_ops.bulk_update_instances.return_value = {}
        return service

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

    def test_import_file_uses_single_chunk_and_explicit_callback(self):
        service = self._make_stubbed_service({"order": [], "models": {}})
        df = pd.DataFrame([{"username": "user1"}])
        callback = Mock()
        service.file_reader.read_file.return_value = df
        service._import_chunk = Mock(return_value={"rows": [], "summary": {}})

        result = service.import_file(Mock(), progress_callback=callback)

        self.assertEqual(result, {"rows": [], "summary": {}})
        service._import_chunk.assert_called_once_with(
            df, 0, callback, total_file_rows=1
        )

    def test_import_file_uses_chunked_mode_when_chunk_size_is_smaller(self):
        service = self._make_stubbed_service(
            {"order": [], "models": {}, "chunk_size": 1}
        )
        df = pd.DataFrame([{"username": "user1"}, {"username": "user2"}])
        service.file_reader.read_file.return_value = df
        service.progress_callback = Mock()
        service._import_in_chunks = Mock(return_value={"rows": ["ok"], "summary": {}})

        result = service.import_file(Mock())

        self.assertEqual(result, {"rows": ["ok"], "summary": {}})
        service._import_in_chunks.assert_called_once_with(df, 1, service.progress_callback)

    def test_get_template_columns_returns_sorted_columns(self):
        service = self._make_stubbed_service()
        service.validator.get_all_columns.return_value = {"email", "username"}

        self.assertEqual(service.get_template_columns(), ["email", "username"])

    @patch("drf_commons.services.import_from_file.service.logger")
    def test_import_in_chunks_aggregates_success_and_failure_results(self, mock_logger):
        service = self._make_stubbed_service({"order": [], "models": {}})
        df = pd.DataFrame([{"row": 1}, {"row": 2}, {"row": 3}, {"row": 4}, {"row": 5}])
        service._import_chunk = Mock(
            side_effect=[
                {
                    "rows": [{"status": "created"}, {"status": "updated"}],
                    "summary": {"created": 1, "updated": 1, "failed": 0, "pending": 0},
                },
                RuntimeError("chunk boom"),
                {
                    "rows": [{"status": "created"}],
                    "summary": {"created": 1, "updated": 0, "failed": 0, "pending": 0},
                },
            ]
        )

        result = service._import_in_chunks(df, chunk_size=2, callback=None)

        self.assertEqual(result["summary"]["total_rows"], 5)
        self.assertEqual(result["summary"]["created"], 2)
        self.assertEqual(result["summary"]["updated"], 1)
        self.assertEqual(result["summary"]["failed"], 2)
        self.assertEqual(len(result["rows"]), 5)
        mock_logger.error.assert_called_once()

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

    def test_import_chunk_marks_existing_object_failed_when_updates_are_disabled(self):
        service = self._make_stubbed_service(
            {
                "order": ["main"],
                "models": {
                    "main": {
                        "model": "auth.User",
                        "unique_by": ["username"],
                        "update_if_exists": False,
                    }
                },
            }
        )
        existing = User.objects.create(username="duplicate", email="old@test.com")
        service.data_processor.prefetch_existing_objects.return_value = {
            ("duplicate",): existing
        }
        service.data_processor.prepare_kwargs_for_row.return_value = {
            "username": "duplicate",
            "email": "new@test.com",
        }
        service.data_processor.get_unique_key.return_value = ("duplicate",)

        result = service._import_chunk(
            pd.DataFrame([{"username": "duplicate", "email": "new@test.com"}]),
            start_row_offset=0,
            callback=None,
            total_file_rows=1,
        )

        row = result["rows"][0]
        self.assertEqual(row["status"], "failed")
        self.assertIn("update_if_exists is False", row["errors"][0])

    def test_import_chunk_reuses_pending_instance_for_same_chunk_duplicates(self):
        service = self._make_stubbed_service(
            {
                "order": ["main"],
                "models": {
                    "main": {
                        "model": "auth.User",
                        "unique_by": ["username"],
                        "update_if_exists": True,
                    }
                },
            }
        )
        service.data_processor.prepare_kwargs_for_row.side_effect = [
            {"username": "duplicate", "email": "first@test.com"},
            {"username": "duplicate", "email": "second@test.com"},
        ]
        service.data_processor.get_unique_key.side_effect = [
            ("duplicate",),
            ("duplicate",),
        ]

        result = service._import_chunk(
            pd.DataFrame(
                [
                    {"username": "duplicate", "email": "first@test.com"},
                    {"username": "duplicate", "email": "second@test.com"},
                ]
            ),
            start_row_offset=0,
            callback=None,
            total_file_rows=2,
        )

        statuses = [row["status"] for row in result["rows"]]
        self.assertEqual(statuses, ["created", "updated"])
        service.bulk_ops.apply_updates.assert_called_once()
        service.bulk_ops.bulk_update_instances.assert_called_once_with(User, [], set())

    def test_import_chunk_formats_import_error_without_field_name(self):
        service = self._make_stubbed_service()
        service.data_processor.prepare_kwargs_for_row.side_effect = ImportErrorRow(
            "row invalid"
        )

        result = service._import_chunk(
            pd.DataFrame([{"username": "bad", "email": "bad@test.com"}]),
            start_row_offset=4,
            callback=None,
            total_file_rows=1,
        )

        self.assertEqual(result["rows"][0]["status"], "failed")
        self.assertIn("Row 5: row invalid", result["rows"][0]["errors"][0])

    def test_import_chunk_handles_unexpected_row_errors_and_progress_callbacks(self):
        service = self._make_stubbed_service()
        callback = Mock()
        service.data_processor.prepare_kwargs_for_row.side_effect = [
            {"username": f"user{i}", "email": f"user{i}@test.com"}
            for i in range(99)
        ] + [RuntimeError("boom")]

        result = service._import_chunk(
            pd.DataFrame(
                [
                    {"username": f"user{i}", "email": f"user{i}@test.com"}
                    for i in range(100)
                ]
            ),
            start_row_offset=0,
            callback=callback,
            total_file_rows=100,
        )

        self.assertEqual(result["rows"][-1]["status"], "failed")
        self.assertIn("Unexpected error - boom", result["rows"][-1]["errors"][0])
        self.assertEqual(callback.call_count, 2)
        callback.assert_any_call(100, 100)

    def test_import_chunk_uses_individual_saves_for_referenced_steps(self):
        service = self._make_stubbed_service()
        service._is_step_referenced_later = Mock(return_value=True)
        service.data_processor.prepare_kwargs_for_row.return_value = {
            "username": "ref-user",
            "email": "ref@test.com",
        }

        service._import_chunk(
            pd.DataFrame([{"username": "ref-user", "email": "ref@test.com"}]),
            start_row_offset=0,
            callback=None,
            total_file_rows=1,
        )

        service.bulk_ops.individual_create_instances.assert_called_once()
        service.bulk_ops.bulk_create_instances.assert_not_called()

    def test_import_chunk_propagates_create_failures_to_duplicate_rows(self):
        service = self._make_stubbed_service(
            {
                "order": ["main"],
                "models": {
                    "main": {
                        "model": "auth.User",
                        "unique_by": ["username"],
                        "update_if_exists": True,
                    }
                },
            }
        )
        service.data_processor.prepare_kwargs_for_row.side_effect = [
            {"username": "duplicate", "email": "first@test.com"},
            {"username": "duplicate", "email": "second@test.com"},
        ]
        service.data_processor.get_unique_key.side_effect = [
            ("duplicate",),
            ("duplicate",),
        ]
        service.bulk_ops.bulk_create_instances.return_value = {0: "db failure"}

        result = service._import_chunk(
            pd.DataFrame(
                [
                    {"username": "duplicate", "email": "first@test.com"},
                    {"username": "duplicate", "email": "second@test.com"},
                ]
            ),
            start_row_offset=0,
            callback=None,
            total_file_rows=2,
        )

        self.assertEqual(result["rows"][0]["status"], "failed")
        self.assertEqual(result["rows"][1]["status"], "failed")
        self.assertIn("db failure", result["rows"][1]["errors"][0])

    def test_summary_reference_detection_and_model_lookup_helpers(self):
        service = self._make_stubbed_service(
            {
                "order": ["parent", "child"],
                "models": {
                    "parent": {"model": "auth.User"},
                    "child": {
                        "model": "auth.User",
                        "reference_fields": {"owner": "parent"},
                    },
                },
            }
        )

        summary = service._build_summary(
            [
                {"status": "created"},
                {"status": "failed"},
                {"status": "updated"},
                {"status": "pending"},
            ],
            total_rows=4,
        )

        self.assertEqual(
            summary,
            {
                "total_rows": 4,
                "created": 1,
                "updated": 1,
                "failed": 1,
                "pending": 1,
            },
        )
        self.assertTrue(service._is_step_referenced_later("parent"))
        self.assertFalse(service._is_step_referenced_later("child"))

        with patch("drf_commons.services.import_from_file.service.apps.get_model", return_value=User) as mock_get_model:
            self.assertIs(service._get_model("auth.User"), User)
            mock_get_model.assert_called_once_with("auth.User")

"""
Tests for ConfigValidator class.

Tests configuration validation functionality.
"""

from unittest.mock import patch

from drf_commons.common_tests.base_cases import DrfCommonTestCase

from ...core.exceptions import ImportValidationError
from ..config_validator import ConfigValidator


class ConfigValidatorTests(DrfCommonTestCase):
    """Tests for ConfigValidator."""

    def setUp(self):
        super().setUp()
        self.valid_config = {
            "file_format": "xlsx",
            "order": ["main"],
            "models": {
                "main": {
                    "model_name": "auth.User",
                    "field_mappings": {
                        "username": {"source": "username"},
                        "email": {"source": "email"},
                    },
                }
            },
        }
        self.transforms = {}

    @staticmethod
    def _minimal_valid_config():
        return {
            "file_format": "xlsx",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "direct_columns": {"username": "username"},
                }
            },
        }

    def test_validator_initialization(self):
        """Test validator initializes with config and transforms."""
        validator = ConfigValidator(self.valid_config, self.transforms)
        self.assertEqual(validator.config, self.valid_config)
        self.assertEqual(validator.transforms, self.transforms)

    def test_validator_initialization_with_transforms(self):
        """Test validator initialization with transform functions."""
        transforms = {"test_field": lambda x: x.upper()}
        validator = ConfigValidator(self.valid_config, transforms)
        self.assertEqual(validator.transforms, transforms)

    @patch.object(ConfigValidator, "_validate_structure")
    @patch.object(ConfigValidator, "_validate_models")
    @patch.object(ConfigValidator, "_validate_field_types")
    @patch.object(ConfigValidator, "_validate_references")
    @patch.object(ConfigValidator, "_validate_transforms")
    def test_validate_calls_all_validation_methods(
        self,
        mock_transforms,
        mock_references,
        mock_field_types,
        mock_models,
        mock_structure,
    ):
        """Test validate method calls all validation methods."""
        validator = ConfigValidator(self.valid_config, self.transforms)
        validator.validate()

        mock_structure.assert_called_once()
        mock_models.assert_called_once()
        mock_field_types.assert_called_once()
        mock_references.assert_called_once()
        mock_transforms.assert_called_once()

    def test_validate_with_invalid_config_structure(self):
        """Test validation fails with invalid config structure."""
        invalid_config = {"invalid": "config"}
        validator = ConfigValidator(invalid_config, self.transforms)

        with self.assertRaises(ImportValidationError):
            validator.validate()

    def test_validate_with_missing_model_name(self):
        """Test validation fails with missing model_name."""
        invalid_config = {
            "file_format": "xlsx",
            "order": ["main"],
            "models": {
                "main": {"field_mappings": {"username": {"source": "username"}}}
            },
        }
        validator = ConfigValidator(invalid_config, self.transforms)

        with self.assertRaises(ImportValidationError):
            validator.validate()

    def test_validate_with_missing_field_mappings(self):
        """Test validation fails with missing field_mappings."""
        invalid_config = {
            "file_format": "xlsx",
            "order": ["main"],
            "models": {"main": {"model_name": "auth.User"}},
        }
        validator = ConfigValidator(invalid_config, self.transforms)

        with self.assertRaises(ImportValidationError):
            validator.validate()

    def test_validate_lookup_field_must_be_database_field(self):
        """Lookup fields must target concrete model fields."""
        invalid_config = {
            "file_format": "xlsx",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "direct_columns": {"username": "username"},
                    "lookup_fields": {
                        "manager": {
                            "column": "username",
                            "model": "auth.User",
                            "lookup_field": "get_full_name",
                        }
                    },
                }
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("lookup_field", str(cm.exception))
        self.assertIn("database field", str(cm.exception))

    def test_validate_lookup_field_accepts_database_field(self):
        """Lookup fields with DB-backed lookup_field pass validation."""
        valid_lookup_config = {
            "file_format": "xlsx",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "direct_columns": {"username": "username"},
                    "lookup_fields": {
                        "manager": {
                            "column": "username",
                            "model": "auth.User",
                            "lookup_field": "username",
                        }
                    },
                }
            },
        }

        validator = ConfigValidator(valid_lookup_config, self.transforms)
        validator.validate()

    def test_validate_rejects_chunk_size_zero(self):
        """chunk_size must be >= 1 when provided."""
        invalid_config = self._minimal_valid_config()
        invalid_config["chunk_size"] = 0

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("chunk_size", str(cm.exception))

    def test_validate_rejects_negative_chunk_size(self):
        """Negative chunk_size values are invalid."""
        invalid_config = self._minimal_valid_config()
        invalid_config["chunk_size"] = -5

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("chunk_size", str(cm.exception))

    def test_validate_rejects_non_integer_chunk_size(self):
        """chunk_size must be an integer, not string/float."""
        invalid_config = self._minimal_valid_config()
        invalid_config["chunk_size"] = "100"

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("chunk_size", str(cm.exception))

    def test_validate_accepts_positive_chunk_size(self):
        """Positive integer chunk_size is accepted."""
        valid_config = self._minimal_valid_config()
        valid_config["chunk_size"] = 100

        validator = ConfigValidator(valid_config, self.transforms)
        validator.validate()

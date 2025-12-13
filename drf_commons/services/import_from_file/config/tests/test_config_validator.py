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

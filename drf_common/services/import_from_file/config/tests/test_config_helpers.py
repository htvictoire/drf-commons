"""
Tests for ConfigHelpers class.

Tests configuration helper functionality.
"""

from drf_common.common_tests.base_cases import DrfCommonTestCase

from ..config_helpers import ConfigHelpers


class ConfigHelpersTests(DrfCommonTestCase):
    """Tests for ConfigHelpers."""

    def test_create_simple_config_basic(self):
        """Test create_simple_config with basic parameters."""
        field_mappings = {"username": "Username", "email": "Email Address"}

        config = ConfigHelpers.create_simple_config("auth.User", field_mappings)

        self.assertIn("file_format", config)
        self.assertEqual(config["file_format"], "xlsx")
        self.assertIn("order", config)
        self.assertEqual(config["order"], ["main"])
        self.assertIn("models", config)
        self.assertIn("main", config["models"])

    def test_create_simple_config_with_file_format(self):
        """Test create_simple_config with custom file format."""
        field_mappings = {"username": "Username"}

        config = ConfigHelpers.create_simple_config(
            "auth.User", field_mappings, file_format="csv"
        )

        self.assertEqual(config["file_format"], "csv")

    def test_create_simple_config_with_unique_by(self):
        """Test create_simple_config with unique_by parameter."""
        field_mappings = {"username": "Username", "email": "Email"}
        unique_by = ["username"]

        config = ConfigHelpers.create_simple_config(
            "auth.User", field_mappings, unique_by=unique_by
        )

        self.assertIn("models", config)
        self.assertIn("main", config["models"])

    def test_create_simple_config_model_structure(self):
        """Test create_simple_config creates correct model structure."""
        field_mappings = {"username": "Username", "email": "Email"}

        config = ConfigHelpers.create_simple_config("auth.User", field_mappings)

        main_model = config["models"]["main"]
        self.assertIn("model", main_model)
        self.assertEqual(main_model["model"], "auth.User")
        self.assertIn("direct_columns", main_model)

    def test_create_simple_config_field_mappings_structure(self):
        """Test create_simple_config creates correct field mappings structure."""
        field_mappings = {"username": "Username", "email": "Email"}

        config = ConfigHelpers.create_simple_config("auth.User", field_mappings)

        mappings = config["models"]["main"]["direct_columns"]
        self.assertIn("username", mappings)
        self.assertIn("email", mappings)

    def test_validate_transforms_needed_basic(self):
        """Test validate_transforms_needed method exists."""
        # Test that the method exists and can be called
        config = {"models": {"main": {"direct_columns": {}}}}
        transforms = {}
        result = ConfigHelpers.validate_transforms_needed(config, transforms)
        # Method should complete without error
        self.assertIsInstance(result, list)

"""
Tests for ConfigValidator class.

Tests configuration validation functionality.
"""

from unittest.mock import patch

from drf_commons.common_tests.base_cases import DrfCommonTestCase

from drf_commons.services.import_from_file.core.exceptions import ImportValidationError
from drf_commons.services.import_from_file.config.config_validator import ConfigValidator


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

    def test_validate_rejects_unsupported_file_format(self):
        """Unsupported file_format values are rejected."""
        invalid_config = self._minimal_valid_config()
        invalid_config["file_format"] = "pdf"

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("Unsupported file format", str(cm.exception))

    def test_validate_rejects_empty_order(self):
        """Empty order list is rejected."""
        invalid_config = self._minimal_valid_config()
        invalid_config["order"] = []

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("order", str(cm.exception))

    def test_validate_rejects_order_step_not_in_models(self):
        """Order referencing a step not in models is rejected."""
        invalid_config = self._minimal_valid_config()
        invalid_config["order"] = ["main", "missing_step"]

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("missing_step", str(cm.exception))

    def test_validate_rejects_invalid_model_path(self):
        """Model with invalid app.Model path raises ImportValidationError."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "nonexistent.Model",
                    "direct_columns": {"name": "name"},
                }
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("Cannot import model", str(cm.exception))

    def test_validate_rejects_transformed_columns_not_dict(self):
        """transformed_columns entry that is not a dict is rejected."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "transformed_columns": {
                        "username": "not_a_dict"
                    },
                }
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("transformed_columns", str(cm.exception))
        self.assertIn("dict", str(cm.exception))

    def test_validate_rejects_transformed_columns_missing_column_key(self):
        """transformed_columns entry missing 'column' key is rejected."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "transformed_columns": {
                        "username": {"transform": "upper_case"}
                    },
                }
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("column", str(cm.exception))

    def test_validate_rejects_transformed_columns_missing_transform_key(self):
        """transformed_columns entry missing 'transform' key is rejected."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "transformed_columns": {
                        "username": {"column": "Username"}
                    },
                }
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("transform", str(cm.exception))

    def test_validate_rejects_lookup_fields_not_dict(self):
        """lookup_fields entry that is not a dict is rejected."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "direct_columns": {"username": "username"},
                    "lookup_fields": {
                        "group": "not_a_dict"
                    },
                }
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("lookup_fields", str(cm.exception))
        self.assertIn("dict", str(cm.exception))

    def test_validate_rejects_lookup_fields_missing_required_key(self):
        """lookup_fields entry missing a required key (column, model, lookup_field) is rejected."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "direct_columns": {"username": "username"},
                    "lookup_fields": {
                        "group": {
                            "column": "group_name",
                            "model": "auth.Group",
                            # missing lookup_field
                        }
                    },
                }
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("lookup_field", str(cm.exception))

    def test_validate_rejects_computed_fields_not_dict(self):
        """computed_fields entry that is not a dict is rejected."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "computed_fields": {
                        "email": "not_a_dict"
                    },
                }
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("computed_fields", str(cm.exception))

    def test_validate_rejects_computed_fields_missing_generator(self):
        """computed_fields entry missing 'generator' key is rejected."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "computed_fields": {
                        "email": {"mode": "always"}
                    },
                }
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("generator", str(cm.exception))

    def test_validate_rejects_computed_fields_invalid_mode(self):
        """computed_fields entry with invalid mode is rejected."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "computed_fields": {
                        "email": {"generator": "gen_email", "mode": "invalid_mode"}
                    },
                }
            },
        }

        validator = ConfigValidator(invalid_config, {"gen_email": lambda **kw: "x"}, )
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("mode", str(cm.exception))

    def test_validate_rejects_required_fields_not_list(self):
        """required_fields that is not a list is rejected."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "direct_columns": {"username": "username"},
                    "required_fields": "username",  # string, not list
                }
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("required_fields", str(cm.exception))
        self.assertIn("list", str(cm.exception))

    def test_validate_rejects_required_fields_undefined_field(self):
        """required_fields referencing undefined field name is rejected."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "direct_columns": {"username": "username"},
                    "required_fields": ["username", "nonexistent_field"],
                }
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("nonexistent_field", str(cm.exception))

    def test_validate_rejects_reference_fields_unknown_step(self):
        """reference_fields referencing unknown step is rejected."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "direct_columns": {"username": "username"},
                    "reference_fields": {"profile": "unknown_step"},
                }
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("unknown_step", str(cm.exception))

    def test_validate_rejects_reference_fields_forward_reference(self):
        """reference_fields referencing a step that comes later in order is rejected."""
        invalid_config = {
            "file_format": "csv",
            "order": ["main", "profile"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "direct_columns": {"username": "username"},
                    "reference_fields": {"profile": "profile"},  # forward reference
                },
                "profile": {
                    "model": "auth.User",
                    "direct_columns": {"email": "email"},
                },
            },
        }

        validator = ConfigValidator(invalid_config, self.transforms)
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("profile", str(cm.exception))

    def test_validate_missing_transforms_detected(self):
        """Missing transform functions referenced in config are reported."""
        config_with_transform = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "transformed_columns": {
                        "username": {"column": "Username", "transform": "missing_fn"}
                    },
                }
            },
        }

        validator = ConfigValidator(config_with_transform, {})  # no transforms provided
        with self.assertRaises(ImportValidationError) as cm:
            validator.validate()

        self.assertIn("missing_fn", str(cm.exception))

    def test_get_missing_transforms_returns_missing_names(self):
        """get_missing_transforms returns names of transforms not provided."""
        config_with_transforms = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "transformed_columns": {
                        "username": {"column": "Username", "transform": "fn_a"}
                    },
                    "computed_fields": {
                        "email": {"generator": "fn_b", "mode": "always"}
                    },
                }
            },
        }

        validator = ConfigValidator(config_with_transforms, {"fn_a": lambda x: x})
        missing = validator.get_missing_transforms()
        self.assertIn("fn_b", missing)
        self.assertNotIn("fn_a", missing)

    def test_get_all_columns_extracts_from_all_field_types(self):
        """get_all_columns extracts columns from direct, transformed, lookup, and computed fields."""
        config = {
            "file_format": "csv",
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "direct_columns": {"username": "Username"},
                    "transformed_columns": {
                        "email": {"column": "Email", "transform": "fn"}
                    },
                    "lookup_fields": {
                        "group": {"column": "Group", "model": "auth.Group", "lookup_field": "name"}
                    },
                    "computed_fields": {
                        "student_id": {"generator": "gen_id", "mode": "if_empty", "column": "StudentID"},
                        "full_gen": {"generator": "gen_full", "mode": "always"},
                    },
                }
            },
        }

        validator = ConfigValidator(config, {})
        columns = validator.get_all_columns()

        self.assertIn("Username", columns)
        self.assertIn("Email", columns)
        self.assertIn("Group", columns)
        self.assertIn("StudentID", columns)
        # "always" mode computed field without a column should NOT be included
        self.assertNotIn("full_gen", columns)

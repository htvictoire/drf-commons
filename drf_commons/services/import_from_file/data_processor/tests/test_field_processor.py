"""
Tests for FieldProcessor class.

Tests field processing functionality.
"""

from unittest.mock import Mock

from drf_commons.common_tests.base_cases import DrfCommonTestCase

from ..field_processor import FieldProcessor


class FieldProcessorTests(DrfCommonTestCase):
    """Tests for FieldProcessor."""

    def setUp(self):
        super().setUp()
        self.transforms = {
            "upper_case": lambda x: x.upper() if isinstance(x, str) else x,
            "add_prefix": lambda x: f"prefix_{x}" if x else x,
        }

    def test_field_processor_initialization(self):
        """Test field processor initializes with transforms."""
        processor = FieldProcessor(self.transforms)
        self.assertEqual(processor.transforms, self.transforms)

    def test_field_processor_with_empty_transforms(self):
        """Test field processor with empty transforms."""
        processor = FieldProcessor({})
        self.assertEqual(processor.transforms, {})

    def test_field_processor_initialization_with_none_transforms(self):
        """Test field processor handles None transforms."""
        processor = FieldProcessor(None)
        # Should handle None gracefully, likely defaulting to empty dict
        self.assertIsNotNone(processor.transforms)

    def test_normalize_cell_value_handles_parser_markers(self):
        """Placeholder values from file parsing should normalize to None."""
        processor = FieldProcessor(self.transforms)

        self.assertIsNone(processor.normalize_cell_value(None))
        self.assertIsNone(processor.normalize_cell_value("nan"))
        self.assertIsNone(processor.normalize_cell_value(" None "))
        self.assertIsNone(processor.normalize_cell_value(float("nan")))
        self.assertEqual(processor.normalize_cell_value("value"), "value")

    def test_process_direct_columns_normalizes_placeholder_values(self):
        """Direct-column mapping should normalize parser placeholders."""
        processor = FieldProcessor(self.transforms)
        row = {"email": "none"}
        model_config = {"direct_columns": {"email": "email"}}
        kwargs = {}

        processor.process_direct_columns(row, model_config, kwargs)

        self.assertIsNone(kwargs["email"])

    def test_process_transformed_columns_skips_transform_for_normalized_null(self):
        """Transforms should not execute when source value normalizes to None."""
        mock_transform = Mock(return_value="SHOULD_NOT_BE_USED")
        processor = FieldProcessor({"upper_case": mock_transform})
        row = {"name": "nan"}
        model_config = {
            "transformed_columns": {
                "name": {"column": "name", "transform": "upper_case"}
            }
        }
        kwargs = {}

        processor.process_transformed_columns(row, model_config, kwargs)

        self.assertIsNone(kwargs["name"])
        mock_transform.assert_not_called()

    def test_process_computed_fields_if_empty_normalizes_placeholder_values(self):
        """Computed if-empty mode should run generator when source normalizes to None."""
        mock_generator = Mock(return_value="generated@example.com")
        processor = FieldProcessor({"gen_email": mock_generator})
        row = {"email": "none"}
        model_config = {
            "computed_fields": {
                "email": {
                    "generator": "gen_email",
                    "mode": "if_empty",
                    "column": "email",
                }
            }
        }
        kwargs = {}

        processor.process_computed_fields(row, model_config, {}, kwargs)

        self.assertEqual(kwargs["email"], "generated@example.com")
        mock_generator.assert_called_once()

    def test_process_lookup_fields_normalizes_placeholder_values(self):
        """Lookup path should normalize parser placeholders before resolution."""
        processor = FieldProcessor(self.transforms)
        lookup_manager = Mock()
        row = {"department": " none "}
        model_config = {
            "lookup_fields": {
                "department": {
                    "column": "department",
                    "model": "auth.Group",
                    "lookup_field": "name",
                    "create_if_missing": True,
                }
            }
        }
        kwargs = {}

        processor.process_lookup_fields(
            row=row,
            model_config=model_config,
            lookup_caches={},
            lookup_manager=lookup_manager,
            kwargs=kwargs,
        )

        self.assertIsNone(kwargs["department"])
        lookup_manager.resolve_lookup.assert_not_called()

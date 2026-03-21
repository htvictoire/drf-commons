"""
Tests for FieldProcessor class.

Tests field processing functionality.
"""

from unittest.mock import Mock

from drf_commons.common_tests.base_cases import DrfCommonTestCase

from drf_commons.services.import_from_file.data_processor.field_processor import FieldProcessor


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


class FieldProcessorTransformExceptionTests(DrfCommonTestCase):
    """Tests for transform exception handling in FieldProcessor."""

    def setUp(self):
        super().setUp()

    def test_apply_transform_raises_value_error_for_missing_transform(self):
        """apply_transform raises ValueError when transform name is not registered."""
        processor = FieldProcessor({"existing_fn": lambda x: x})

        with self.assertRaises(ValueError) as cm:
            processor.apply_transform("nonexistent_fn", "value")

        self.assertIn("nonexistent_fn", str(cm.exception))

    def test_apply_transform_raises_value_error_when_function_throws(self):
        """apply_transform wraps transform function exceptions in ValueError."""
        def bad_fn(x):
            raise RuntimeError("internal error")

        processor = FieldProcessor({"bad_fn": bad_fn})

        with self.assertRaises(ValueError) as cm:
            processor.apply_transform("bad_fn", "value")

        self.assertIn("bad_fn", str(cm.exception))
        self.assertIn("internal error", str(cm.exception))

    def test_process_transformed_columns_wraps_transform_exception(self):
        """process_transformed_columns wraps ValueError from apply_transform in ImportErrorRow."""
        from drf_commons.services.import_from_file.core.exceptions import ImportErrorRow

        def bad_fn(x):
            raise RuntimeError("transform crash")

        processor = FieldProcessor({"bad_fn": bad_fn})
        row = {"col": "some_value"}
        model_config = {
            "transformed_columns": {
                "field_a": {"column": "col", "transform": "bad_fn"}
            }
        }
        kwargs = {}

        with self.assertRaises(ImportErrorRow):
            processor.process_transformed_columns(row, model_config, kwargs)


class FieldProcessorReferenceFieldTests(DrfCommonTestCase):
    """Tests for reference_fields validation in FieldProcessor."""

    def setUp(self):
        super().setUp()
        self.processor = FieldProcessor({})

    def test_process_reference_fields_skips_when_no_reference_fields(self):
        """process_reference_fields does nothing when no reference_fields in config."""
        kwargs = {}
        self.processor.process_reference_fields({}, {}, kwargs)
        self.assertEqual(kwargs, {})

    def test_process_reference_fields_raises_when_ref_object_missing(self):
        """process_reference_fields raises ImportErrorRow when referenced step object is absent."""
        from drf_commons.services.import_from_file.core.exceptions import ImportErrorRow

        model_config = {"reference_fields": {"profile": "profile_step"}}
        created_objs = {}  # profile_step not in here
        kwargs = {}

        with self.assertRaises(ImportErrorRow) as cm:
            self.processor.process_reference_fields(model_config, created_objs, kwargs)

        self.assertIn("profile_step", str(cm.exception))

    def test_process_reference_fields_raises_when_ref_has_no_pk_attr(self):
        """process_reference_fields raises ImportErrorRow when ref object has no pk attribute."""
        from drf_commons.services.import_from_file.core.exceptions import ImportErrorRow

        class NoPkObj:
            pass  # no pk attribute

        model_config = {"reference_fields": {"profile": "profile_step"}}
        created_objs = {"profile_step": NoPkObj()}
        kwargs = {}

        with self.assertRaises(ImportErrorRow) as cm:
            self.processor.process_reference_fields(model_config, created_objs, kwargs)

        self.assertIn("profile_step", str(cm.exception))

    def test_process_reference_fields_raises_when_ref_pk_is_none(self):
        """process_reference_fields raises ImportErrorRow when ref object pk is None."""
        from drf_commons.services.import_from_file.core.exceptions import ImportErrorRow

        class UnsavedObj:
            pk = None

        model_config = {"reference_fields": {"profile": "profile_step"}}
        created_objs = {"profile_step": UnsavedObj()}
        kwargs = {}

        with self.assertRaises(ImportErrorRow) as cm:
            self.processor.process_reference_fields(model_config, created_objs, kwargs)

        self.assertIn("profile_step", str(cm.exception))

    def test_process_reference_fields_sets_kwargs_for_valid_ref(self):
        """process_reference_fields sets kwargs field to the referenced object."""

        class SavedObj:
            pk = 42

        obj = SavedObj()
        model_config = {"reference_fields": {"profile": "profile_step"}}
        created_objs = {"profile_step": obj}
        kwargs = {}

        self.processor.process_reference_fields(model_config, created_objs, kwargs)

        self.assertIs(kwargs["profile"], obj)


class FieldProcessorLookupFieldTests(DrfCommonTestCase):
    """Tests for lookup_fields full resolution paths in FieldProcessor."""

    def setUp(self):
        super().setUp()
        self.processor = FieldProcessor({})

    def test_process_lookup_fields_skips_when_no_lookup_fields(self):
        """process_lookup_fields does nothing when no lookup_fields in config."""
        kwargs = {}
        self.processor.process_lookup_fields({}, {}, {}, Mock(), kwargs)
        self.assertEqual(kwargs, {})

    def test_process_lookup_fields_sets_found_object(self):
        """process_lookup_fields sets kwargs to resolved object when lookup succeeds."""
        from unittest.mock import Mock

        mock_lookup_manager = Mock()
        found_obj = Mock()
        mock_lookup_manager.resolve_lookup.return_value = found_obj

        model_config = {
            "lookup_fields": {
                "group": {
                    "column": "group_name",
                    "model": "auth.Group",
                    "lookup_field": "name",
                }
            }
        }
        row = {"group_name": "admins"}
        kwargs = {}

        self.processor.process_lookup_fields(row, model_config, {}, mock_lookup_manager, kwargs)

        self.assertIs(kwargs["group"], found_obj)

    def test_process_lookup_fields_raises_when_not_found_and_no_create(self):
        """process_lookup_fields raises ImportErrorRow when not found and create_if_missing is False."""
        from unittest.mock import Mock
        from drf_commons.services.import_from_file.core.exceptions import ImportErrorRow

        mock_lookup_manager = Mock()
        mock_lookup_manager.resolve_lookup.return_value = None

        model_config = {
            "lookup_fields": {
                "group": {
                    "column": "group_name",
                    "model": "auth.Group",
                    "lookup_field": "name",
                    "create_if_missing": False,
                }
            }
        }
        row = {"group_name": "nonexistent"}
        kwargs = {}

        with self.assertRaises(ImportErrorRow):
            self.processor.process_lookup_fields(row, model_config, {}, mock_lookup_manager, kwargs)

    def test_process_lookup_fields_create_if_missing_exception_wraps_as_import_error(self):
        """process_lookup_fields wraps get_or_create exception in ImportErrorRow."""
        from unittest.mock import Mock, patch
        from drf_commons.services.import_from_file.core.exceptions import ImportErrorRow

        mock_lookup_manager = Mock()
        mock_lookup_manager.resolve_lookup.return_value = None

        mock_model_cls = Mock()
        mock_model_cls.objects.get_or_create.side_effect = Exception("db error")
        mock_lookup_manager._get_model.return_value = mock_model_cls

        model_config = {
            "lookup_fields": {
                "group": {
                    "column": "group_name",
                    "model": "auth.Group",
                    "lookup_field": "name",
                    "create_if_missing": True,
                }
            }
        }
        row = {"group_name": "new_group"}
        kwargs = {}

        with self.assertRaises(ImportErrorRow) as cm:
            self.processor.process_lookup_fields(row, model_config, {}, mock_lookup_manager, kwargs)

        self.assertIn("db error", str(cm.exception))


class FieldProcessorValidateRequiredTests(DrfCommonTestCase):
    """Tests for validate_required_fields in FieldProcessor."""

    def setUp(self):
        super().setUp()
        self.processor = FieldProcessor({})

    def test_validate_required_fields_skips_when_no_required_fields(self):
        """validate_required_fields does nothing when required_fields not in config."""
        # Should not raise
        self.processor.validate_required_fields({"username": "bob"}, {})

    def test_validate_required_fields_passes_when_all_present(self):
        """validate_required_fields passes when all required fields have values."""
        model_config = {"required_fields": ["username", "email"]}
        kwargs = {"username": "bob", "email": "bob@example.com"}
        # Should not raise
        self.processor.validate_required_fields(kwargs, model_config)

    def test_validate_required_fields_raises_for_empty_string_value(self):
        """validate_required_fields treats empty string as missing."""
        from drf_commons.services.import_from_file.core.exceptions import ImportErrorRow

        model_config = {"required_fields": ["username", "email"]}
        kwargs = {"username": "bob", "email": ""}

        with self.assertRaises(ImportErrorRow) as cm:
            self.processor.validate_required_fields(kwargs, model_config)

        self.assertIn("email", str(cm.exception))

    def test_validate_required_fields_reports_all_missing(self):
        """validate_required_fields includes all missing field names in the error."""
        from drf_commons.services.import_from_file.core.exceptions import ImportErrorRow

        model_config = {"required_fields": ["username", "email", "first_name"]}
        kwargs = {}  # all missing

        with self.assertRaises(ImportErrorRow) as cm:
            self.processor.validate_required_fields(kwargs, model_config)

        error_msg = str(cm.exception)
        self.assertIn("username", error_msg)
        self.assertIn("email", error_msg)
        self.assertIn("first_name", error_msg)

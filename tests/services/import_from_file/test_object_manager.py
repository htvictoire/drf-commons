"""
Tests for ObjectManager class.

Tests object management functionality.
"""


from drf_commons.common_tests.base_cases import DrfCommonTestCase

from drf_commons.services.import_from_file.data_processor.object_manager import ObjectManager


class ObjectManagerTests(DrfCommonTestCase):
    """Tests for ObjectManager."""

    def setUp(self):
        super().setUp()
        self.transforms = {
            "test_transform": lambda x: x.upper() if isinstance(x, str) else x
        }

    def test_object_manager_initialization(self):
        """Test object manager initializes with transforms."""
        manager = ObjectManager(self.transforms)
        self.assertEqual(manager.transforms, self.transforms)

    def test_object_manager_with_empty_transforms(self):
        """Test object manager with empty transforms."""
        manager = ObjectManager({})
        self.assertEqual(manager.transforms, {})

    def test_object_manager_initialization_with_none_transforms(self):
        """Test object manager handles None transforms."""
        manager = ObjectManager(None)
        # Should handle None gracefully
        self.assertIsNotNone(manager.transforms)

    def test_get_unique_key_returns_tuple_for_complete_kwargs(self):
        """Unique key builder should return tuple when all fields are present."""
        manager = ObjectManager({})
        key = manager.get_unique_key(
            ["username", "email"], {"username": "u1", "email": "e1@test.com"}
        )
        self.assertEqual(key, ("u1", "e1@test.com"))

    def test_get_unique_key_returns_none_when_missing_value(self):
        """Unique key builder should return None when any unique field is missing/None."""
        manager = ObjectManager({})
        self.assertIsNone(
            manager.get_unique_key(["username", "email"], {"username": "u1"})
        )
        self.assertIsNone(
            manager.get_unique_key(
                ["username", "email"], {"username": "u1", "email": None}
            )
        )


class ObjectManagerFindExistingTests(DrfCommonTestCase):
    """Tests for find_existing_obj in ObjectManager."""

    def setUp(self):
        super().setUp()
        self.manager = ObjectManager({})

    def test_find_existing_obj_returns_none_when_key_is_none(self):
        """find_existing_obj returns None when unique key cannot be built."""
        existing_map = {("bob",): object()}
        result = self.manager.find_existing_obj(existing_map, ["username"], {"username": None})
        self.assertIsNone(result)

    def test_find_existing_obj_returns_object_when_key_matches(self):
        """find_existing_obj returns matching object from existing_map."""
        mock_obj = object()
        existing_map = {("bob",): mock_obj}
        result = self.manager.find_existing_obj(existing_map, ["username"], {"username": "bob"})
        self.assertIs(result, mock_obj)

    def test_find_existing_obj_returns_none_when_key_not_in_map(self):
        """find_existing_obj returns None when key not present in existing_map."""
        existing_map = {("alice",): object()}
        result = self.manager.find_existing_obj(existing_map, ["username"], {"username": "charlie"})
        self.assertIsNone(result)


class ObjectManagerApplyTransformTests(DrfCommonTestCase):
    """Tests for apply_transform in ObjectManager."""

    def setUp(self):
        super().setUp()

    def test_apply_transform_raises_when_transform_missing(self):
        """apply_transform raises ValueError when transform not registered."""
        manager = ObjectManager({})
        with self.assertRaises(ValueError) as cm:
            manager.apply_transform("missing_fn", "value")
        self.assertIn("missing_fn", str(cm.exception))

    def test_apply_transform_raises_when_function_throws(self):
        """apply_transform wraps exceptions from transform function in ValueError."""
        def crashing_fn(x):
            raise RuntimeError("crash!")

        manager = ObjectManager({"crashing_fn": crashing_fn})
        with self.assertRaises(ValueError) as cm:
            manager.apply_transform("crashing_fn", "value")
        self.assertIn("crashing_fn", str(cm.exception))
        self.assertIn("crash!", str(cm.exception))

    def test_apply_transform_returns_transformed_value(self):
        """apply_transform returns the result of the transform function."""
        manager = ObjectManager({"upper": lambda x: x.upper()})
        result = manager.apply_transform("upper", "hello")
        self.assertEqual(result, "HELLO")


class ObjectManagerPrefetchTests(DrfCommonTestCase):
    """Tests for prefetch_existing_objects in ObjectManager."""

    def setUp(self):
        super().setUp()

    def test_prefetch_uses_direct_columns_to_build_key(self):
        """prefetch_existing_objects reads field value from direct_columns mapping."""
        import pandas as pd
        from unittest.mock import patch, MagicMock

        manager = ObjectManager({})
        model_config = {
            "direct_columns": {"username": "Username"}
        }
        df = pd.DataFrame({"Username": ["alice", "bob"]})

        mock_model = MagicMock()
        mock_model.objects.filter.return_value = []

        result = manager.prefetch_existing_objects(mock_model, ["username"], model_config, df)
        mock_model.objects.filter.assert_called_once()
        self.assertIsInstance(result, dict)

    def test_prefetch_skips_row_when_unique_value_is_none(self):
        """prefetch_existing_objects skips rows where unique field value is None."""
        import pandas as pd
        from unittest.mock import MagicMock

        manager = ObjectManager({})
        model_config = {"direct_columns": {"username": "Username"}}
        df = pd.DataFrame({"Username": [None]})

        mock_model = MagicMock()
        mock_model.objects.filter.return_value = []

        result = manager.prefetch_existing_objects(mock_model, ["username"], model_config, df)
        # No valid keys so filter should not be called with Q objects (empty Q is falsy)
        self.assertEqual(result, {})

    def test_prefetch_applies_transform_for_transformed_columns(self):
        """prefetch_existing_objects applies transform when field is in transformed_columns."""
        import pandas as pd
        from unittest.mock import MagicMock

        manager = ObjectManager({"upper": lambda x: x.upper()})
        model_config = {
            "transformed_columns": {
                "username": {"column": "Username", "transform": "upper"}
            }
        }
        df = pd.DataFrame({"Username": ["alice"]})

        mock_model = MagicMock()
        mock_obj = MagicMock()
        mock_obj.username = "ALICE"
        mock_model.objects.filter.return_value = [mock_obj]

        result = manager.prefetch_existing_objects(mock_model, ["username"], model_config, df)
        mock_model.objects.filter.assert_called_once()

    def test_prefetch_uses_constant_fields(self):
        """prefetch_existing_objects uses constant field value when field is in constant_fields."""
        import pandas as pd
        from unittest.mock import MagicMock

        manager = ObjectManager({})
        model_config = {
            "direct_columns": {"username": "Username"},
            "constant_fields": {"is_active": True},
        }
        df = pd.DataFrame({"Username": ["alice"]})

        mock_model = MagicMock()
        mock_model.objects.filter.return_value = []

        result = manager.prefetch_existing_objects(
            mock_model, ["username", "is_active"], model_config, df
        )
        mock_model.objects.filter.assert_called_once()

    def test_prefetch_raises_when_transform_fails_for_unique_by_field(self):
        """prefetch_existing_objects raises ImportErrorRow when transform fails for a unique_by field."""
        import pandas as pd
        from drf_commons.services.import_from_file.core.exceptions import ImportErrorRow
        from unittest.mock import MagicMock

        def bad_fn(x):
            raise ValueError("bad value")

        manager = ObjectManager({"bad_fn": bad_fn})
        model_config = {
            "transformed_columns": {
                "username": {"column": "Username", "transform": "bad_fn"}
            }
        }
        df = pd.DataFrame({"Username": ["alice"]})
        mock_model = MagicMock()

        with self.assertRaises(ImportErrorRow):
            manager.prefetch_existing_objects(mock_model, ["username"], model_config, df)

    def test_prefetch_handles_nan_value_in_computed_field_column(self):
        """prefetch_existing_objects normalizes NaN values in computed field columns."""
        import pandas as pd
        import numpy as np
        from unittest.mock import MagicMock

        mock_gen = MagicMock(return_value="generated_id")
        manager = ObjectManager({"gen_id": mock_gen})
        model_config = {
            "computed_fields": {
                "student_id": {
                    "generator": "gen_id",
                    "mode": "if_empty",
                    "column": "StudentID",
                }
            }
        }
        df = pd.DataFrame({"StudentID": [float("nan")]})
        mock_model = MagicMock()
        mock_model.objects.filter.return_value = []

        result = manager.prefetch_existing_objects(
            mock_model, ["student_id"], model_config, df
        )
        mock_gen.assert_called()

    def test_prefetch_skips_field_not_in_any_config(self):
        """prefetch_existing_objects skips rows when unique_by field not found in any config."""
        import pandas as pd
        from unittest.mock import MagicMock

        manager = ObjectManager({})
        model_config = {"direct_columns": {"email": "Email"}}  # username not here
        df = pd.DataFrame({"Email": ["a@example.com"]})

        mock_model = MagicMock()

        result = manager.prefetch_existing_objects(mock_model, ["username"], model_config, df)
        # No valid keys
        self.assertEqual(result, {})

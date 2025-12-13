"""
Tests for DataProcessor class.

Tests main data processing functionality.
"""

from unittest.mock import Mock, patch

import pandas as pd

from drf_common.common_tests.base_cases import DrfCommonTestCase

from ..data_processor import DataProcessor


class DataProcessorTests(DrfCommonTestCase):
    """Tests for DataProcessor."""

    def setUp(self):
        super().setUp()
        self.config = {
            "models": {
                "main": {
                    "model_name": "auth.User",
                    "field_mappings": {
                        "username": {"source": "username"},
                        "email": {"source": "email"},
                    },
                }
            }
        }
        self.transforms = {"test_field": lambda x: x.upper()}

    def test_processor_initialization(self):
        """Test processor initializes with config and transforms."""
        processor = DataProcessor(self.config, self.transforms)
        self.assertEqual(processor.config, self.config)
        self.assertEqual(processor.transforms, self.transforms)

    @patch("services.import_from_file.data_processor.data_processor.LookupManager")
    @patch("services.import_from_file.data_processor.data_processor.FieldProcessor")
    @patch("services.import_from_file.data_processor.data_processor.ObjectManager")
    def test_processor_initializes_managers(
        self, mock_object_manager, mock_field_processor, mock_lookup_manager
    ):
        """Test processor initializes all required managers."""
        DataProcessor(self.config, self.transforms)

        mock_lookup_manager.assert_called_once_with(self.config)
        mock_field_processor.assert_called_once_with(self.transforms)
        mock_object_manager.assert_called_once_with(self.transforms)

    def test_collect_lookup_values_with_dataframe(self):
        """Test collect_lookup_values method with DataFrame."""
        df = pd.DataFrame(
            {
                "username": ["user1", "user2"],
                "email": ["user1@example.com", "user2@example.com"],
            }
        )

        processor = DataProcessor(self.config, self.transforms)

        # Mock the lookup manager method
        processor.lookup_manager = Mock()
        processor.lookup_manager.collect_lookup_values = Mock(
            return_value={"test": {"value1", "value2"}}
        )

        result = processor.collect_lookup_values(df)

        processor.lookup_manager.collect_lookup_values.assert_called_once_with(df)
        self.assertEqual(result, {"test": {"value1", "value2"}})

    def test_processor_has_required_managers(self):
        """Test processor has all required manager instances."""
        processor = DataProcessor(self.config, self.transforms)

        self.assertIsNotNone(processor.lookup_manager)
        self.assertIsNotNone(processor.field_processor)
        self.assertIsNotNone(processor.object_manager)

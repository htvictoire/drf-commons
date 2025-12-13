"""
Tests for FieldProcessor class.

Tests field processing functionality.
"""

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

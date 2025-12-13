"""
Tests for ObjectManager class.

Tests object management functionality.
"""


from drf_common.common_tests.base_cases import DrfCommonTestCase

from ..object_manager import ObjectManager


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

"""
Tests for LookupManager class.

Tests lookup management functionality.
"""


import pandas as pd

from drf_common.common_tests.base_cases import DrfCommonTestCase

from ..lookup_manager import LookupManager


class LookupManagerTests(DrfCommonTestCase):
    """Tests for LookupManager."""

    def setUp(self):
        super().setUp()
        self.config = {
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "direct_columns": {
                        "username": "username",
                        "email": "email",
                    },
                }
            }
        }

    def test_lookup_manager_initialization(self):
        """Test lookup manager initializes with config."""
        manager = LookupManager(self.config)
        self.assertEqual(manager.config, self.config)

    def test_collect_lookup_values_with_dataframe(self):
        """Test collect_lookup_values method with DataFrame."""
        df = pd.DataFrame(
            {
                "username": ["user1", "user2"],
                "email": ["user1@example.com", "user2@example.com"],
            }
        )

        manager = LookupManager(self.config)
        result = manager.collect_lookup_values(df)

        self.assertIsInstance(result, dict)

    def test_collect_lookup_values_with_empty_dataframe(self):
        """Test collect_lookup_values with empty DataFrame."""
        df = pd.DataFrame()
        manager = LookupManager(self.config)
        result = manager.collect_lookup_values(df)

        self.assertIsInstance(result, dict)

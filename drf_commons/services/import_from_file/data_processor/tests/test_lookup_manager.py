"""
Tests for LookupManager class.

Tests lookup management functionality.
"""


import pandas as pd
from django.contrib.auth import get_user_model

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.common_tests.factories import UserFactory

from ...core.exceptions import ImportValidationError
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

    def test_prefetch_lookups_raises_for_non_model_lookup_field(self):
        """Lookup prefetch rejects non-database lookup fields."""
        manager = LookupManager(self.config)
        lookup_values = {"auth.User__get_full_name": {"alice"}}

        with self.assertRaises(ImportValidationError):
            manager.prefetch_lookups(lookup_values)

    def test_prefetch_lookups_uses_database_field_filtering(self):
        """Lookup prefetch should use ORM field filtering for model fields."""
        User = get_user_model()
        user = UserFactory(username="lookup_user")

        manager = LookupManager(self.config)
        lookup_values = {"auth.User__username": {"lookup_user"}}
        caches = manager.prefetch_lookups(lookup_values)

        self.assertIn("auth.User__username", caches)
        self.assertEqual(caches["auth.User__username"]["lookup_user"].pk, user.pk)

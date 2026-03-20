"""
Tests for LookupManager class.

Tests lookup management functionality.
"""


import pandas as pd

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.common_tests.factories import UserFactory

from drf_commons.services.import_from_file.core.exceptions import ImportValidationError
from drf_commons.services.import_from_file.data_processor.lookup_manager import LookupManager


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
        user = UserFactory(username="lookup_user")

        manager = LookupManager(self.config)
        lookup_values = {"auth.User__username": {"lookup_user"}}
        caches = manager.prefetch_lookups(lookup_values)

        self.assertIn("auth.User__username", caches)
        self.assertEqual(caches["auth.User__username"]["lookup_user"].pk, user.pk)

    def test_collect_lookup_values_with_lookup_fields_in_config(self):
        config = {
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "lookup_fields": {
                        "group": {
                            "column": "group_name",
                            "model": "auth.Group",
                            "lookup_field": "name",
                        }
                    },
                }
            },
        }
        df = pd.DataFrame({"group_name": ["admins", "editors", "admins"]})
        manager = LookupManager(config)
        result = manager.collect_lookup_values(df)
        self.assertIn("auth.Group__name", result)
        self.assertEqual(result["auth.Group__name"], {"admins", "editors"})

    def test_collect_lookup_values_raises_for_unqualified_model_path(self):
        config = {
            "order": ["main"],
            "models": {
                "main": {
                    "model": "auth.User",
                    "lookup_fields": {
                        "group": {
                            "column": "group_name",
                            "model": "Group",
                            "lookup_field": "name",
                        }
                    },
                }
            },
        }
        df = pd.DataFrame({"group_name": ["admins"]})
        manager = LookupManager(config)
        with self.assertRaises(ValueError):
            manager.collect_lookup_values(df)

    def test_resolve_lookup_returns_cached_object(self):
        user = UserFactory(username="cached_user")
        manager = LookupManager(self.config)
        lookup_spec = {"model": "auth.User", "lookup_field": "username"}
        caches = {"auth.User__username": {"cached_user": user}}
        result = manager.resolve_lookup(lookup_spec, "cached_user", caches)
        self.assertEqual(result, user)

    def test_resolve_lookup_returns_none_for_missing_value(self):
        manager = LookupManager(self.config)
        lookup_spec = {"model": "auth.User", "lookup_field": "username"}
        caches = {"auth.User__username": {}}
        result = manager.resolve_lookup(lookup_spec, "ghost", caches)
        self.assertIsNone(result)

    def test_resolve_lookup_raises_for_unqualified_model_path(self):
        manager = LookupManager(self.config)
        lookup_spec = {"model": "User", "lookup_field": "username"}
        with self.assertRaises(ValueError):
            manager.resolve_lookup(lookup_spec, "anyone", {})

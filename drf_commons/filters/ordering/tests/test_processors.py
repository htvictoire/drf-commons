"""
Tests for ordering processors.
"""

from django.db import models
from django.test import TestCase

from ..processors import (
    parse_order_field,
    process_aggregate_lookup,
    process_computed_field,
    process_list_lookup,
    process_ordering,
    process_string_lookup,
)


class ParseOrderFieldTests(TestCase):
    """Tests for parse_order_field function."""

    def test_ascending_order(self):
        """Test parsing ascending order field."""
        field_name, is_reverse = parse_order_field("name")
        self.assertEqual(field_name, "name")
        self.assertFalse(is_reverse)

    def test_descending_order(self):
        """Test parsing descending order field."""
        field_name, is_reverse = parse_order_field("-name")
        self.assertEqual(field_name, "name")
        self.assertTrue(is_reverse)

    def test_multiple_dashes(self):
        """Test parsing field with multiple leading dashes."""
        field_name, is_reverse = parse_order_field("--name")
        self.assertEqual(field_name, "-name")
        self.assertTrue(is_reverse)


class ProcessStringLookupTests(TestCase):
    """Tests for process_string_lookup function."""

    def test_ascending_string_lookup(self):
        """Test processing ascending string lookup."""
        result = process_string_lookup("related__name", False)
        self.assertEqual(result, ["related__name"])

    def test_descending_string_lookup(self):
        """Test processing descending string lookup."""
        result = process_string_lookup("related__name", True)
        self.assertEqual(result, ["-related__name"])


class ProcessListLookupTests(TestCase):
    """Tests for process_list_lookup function."""

    def test_ascending_list_lookup(self):
        """Test processing ascending list lookup."""
        lookup = ["first_name", "last_name"]
        result = process_list_lookup(lookup, False)
        self.assertEqual(result, ["first_name", "last_name"])

    def test_descending_list_lookup(self):
        """Test processing descending list lookup."""
        lookup = ["first_name", "last_name"]
        result = process_list_lookup(lookup, True)
        self.assertEqual(result, ["-first_name", "-last_name"])

    def test_empty_list_lookup(self):
        """Test processing empty list lookup."""
        result = process_list_lookup([], False)
        self.assertEqual(result, [])


class ProcessAggregateLookupTests(TestCase):
    """Tests for process_aggregate_lookup function."""

    def test_ascending_aggregate_lookup(self):
        """Test processing ascending aggregate lookup."""
        lookup = models.Count("items")
        result_fields, annotation = process_aggregate_lookup(
            lookup, "item_count", False
        )

        self.assertEqual(result_fields, ["item_count_order"])
        self.assertIn("item_count_order", annotation)
        self.assertEqual(annotation["item_count_order"], lookup)

    def test_descending_aggregate_lookup(self):
        """Test processing descending aggregate lookup."""
        lookup = models.Count("items")
        result_fields, annotation = process_aggregate_lookup(lookup, "item_count", True)

        self.assertEqual(result_fields, ["-item_count_order"])
        self.assertIn("item_count_order", annotation)
        self.assertEqual(annotation["item_count_order"], lookup)


class ProcessComputedFieldTests(TestCase):
    """Tests for process_computed_field function."""

    def test_string_computed_field(self):
        """Test processing string computed field."""
        ordering_fields, annotations = process_computed_field(
            "test", "related__name", False
        )
        self.assertEqual(ordering_fields, ["related__name"])
        self.assertEqual(annotations, {})

    def test_list_computed_field(self):
        """Test processing list computed field."""
        lookup = ["first_name", "last_name"]
        ordering_fields, annotations = process_computed_field("test", lookup, True)
        self.assertEqual(ordering_fields, ["-first_name", "-last_name"])
        self.assertEqual(annotations, {})

    def test_aggregate_computed_field(self):
        """Test processing aggregate computed field."""
        lookup = models.Count("items")
        ordering_fields, annotations = process_computed_field(
            "item_count", lookup, False
        )
        self.assertEqual(ordering_fields, ["item_count_order"])
        self.assertIn("item_count_order", annotations)

    def test_unsupported_lookup_type(self):
        """Test processing unsupported lookup type raises error."""
        with self.assertRaises(ValueError) as cm:
            process_computed_field("test", 42, False)
        self.assertIn("Unsupported lookup type", str(cm.exception))


class ProcessOrderingTests(TestCase):
    """Tests for process_ordering function."""

    def test_empty_ordering(self):
        """Test processing empty ordering list."""
        processed_ordering, annotations = process_ordering([], {})
        self.assertEqual(processed_ordering, [])
        self.assertEqual(annotations, {})

    def test_no_computed_fields(self):
        """Test processing ordering with no computed fields."""
        ordering = ["name", "-created_at"]
        processed_ordering, annotations = process_ordering(ordering, {})
        self.assertEqual(processed_ordering, ["name", "-created_at"])
        self.assertEqual(annotations, {})

    def test_regular_fields_only(self):
        """Test processing ordering with regular fields only."""
        ordering = ["name", "-created_at"]
        computed_fields = {"custom_field": "related__name"}
        processed_ordering, annotations = process_ordering(ordering, computed_fields)
        self.assertEqual(processed_ordering, ["name", "-created_at"])
        self.assertEqual(annotations, {})

    def test_mixed_fields(self):
        """Test processing ordering with mix of regular and computed fields."""
        ordering = ["name", "-computed_field", "created_at"]
        computed_fields = {
            "computed_field": "related__name",
        }
        processed_ordering, annotations = process_ordering(ordering, computed_fields)
        self.assertEqual(processed_ordering, ["name", "-related__name", "created_at"])
        self.assertEqual(annotations, {})

    def test_multiple_computed_fields(self):
        """Test processing ordering with multiple computed fields."""
        ordering = ["-student", "count_field"]
        computed_fields = {
            "student": ["first_name", "last_name"],
            "count_field": models.Count("items"),
        }
        processed_ordering, annotations = process_ordering(ordering, computed_fields)

        expected_ordering = ["-first_name", "-last_name", "count_field_order"]
        self.assertEqual(processed_ordering, expected_ordering)
        self.assertIn("count_field_order", annotations)

"""
Tests for export utility functions.
"""

from types import SimpleNamespace

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.services.export_file.utils import (
    extract_nested_value,
    get_column_alignment,
    get_column_label,
    sanitize_spreadsheet_cell,
)


class ExtractNestedValueTests(DrfCommonTestCase):
    """Tests for extract_nested_value."""

    def test_simple_field(self):
        self.assertEqual(extract_nested_value({"name": "Alice"}, "name"), "Alice")

    def test_simple_field_missing(self):
        self.assertIsNone(extract_nested_value({"name": "Alice"}, "age"))

    def test_nested_dict(self):
        data = {"a": {"b": 42}}
        self.assertEqual(extract_nested_value(data, "a.b"), 42)

    def test_nested_dict_missing_key(self):
        data = {"a": {}}
        self.assertIsNone(extract_nested_value(data, "a.b"))

    def test_object_attribute_traversal(self):
        obj = SimpleNamespace(profile=SimpleNamespace(bio="hello"))
        data = {"user": obj}
        self.assertEqual(extract_nested_value(data, "user.profile.bio"), "hello")

    def test_missing_attribute_returns_none(self):
        obj = SimpleNamespace(name="test")
        data = {"user": obj}
        self.assertIsNone(extract_nested_value(data, "user.missing"))

    def test_complex_object_converts_to_str(self):
        from datetime import datetime
        dt = datetime(2026, 1, 1, 12, 0, 0)
        data = {"ts": {"value": dt}}
        result = extract_nested_value(data, "ts.value")
        self.assertIsInstance(result, str)

    def test_primitive_returned_as_is(self):
        data = {"count": 5}
        self.assertEqual(extract_nested_value(data, "count"), 5)

    def test_bool_returned_as_is(self):
        data = {"active": True}
        self.assertIs(extract_nested_value(data, "active"), True)

    def test_none_value_returned_as_none(self):
        data = {"a": {"b": None}}
        self.assertIsNone(extract_nested_value(data, "a.b"))


class SanitizeSpreadsheetCellTests(DrfCommonTestCase):
    """Tests for sanitize_spreadsheet_cell."""

    def test_formula_prefix_equals(self):
        self.assertEqual(sanitize_spreadsheet_cell("=SUM(A1)"), "'=SUM(A1)")

    def test_formula_prefix_plus(self):
        self.assertEqual(sanitize_spreadsheet_cell("+1234"), "'+1234")

    def test_formula_prefix_minus(self):
        self.assertEqual(sanitize_spreadsheet_cell("-1234"), "'-1234")

    def test_formula_prefix_at(self):
        self.assertEqual(sanitize_spreadsheet_cell("@user"), "'@user")

    def test_safe_string_unchanged(self):
        self.assertEqual(sanitize_spreadsheet_cell("hello"), "hello")

    def test_non_string_unchanged(self):
        self.assertEqual(sanitize_spreadsheet_cell(42), 42)
        self.assertIsNone(sanitize_spreadsheet_cell(None))

    def test_whitespace_only_unchanged(self):
        self.assertEqual(sanitize_spreadsheet_cell("   "), "   ")

    def test_empty_string_unchanged(self):
        self.assertEqual(sanitize_spreadsheet_cell(""), "")

    def test_leading_whitespace_before_safe_char_unchanged(self):
        self.assertEqual(sanitize_spreadsheet_cell("  hello"), "  hello")

    def test_leading_whitespace_before_dangerous_prefix(self):
        result = sanitize_spreadsheet_cell("  =formula")
        self.assertEqual(result, "'  =formula")


class GetColumnLabelTests(DrfCommonTestCase):
    """Tests for get_column_label."""

    def test_returns_configured_label(self):
        config = {"name": {"label": "Full Name"}}
        self.assertEqual(get_column_label("name", config), "Full Name")

    def test_falls_back_to_title_case(self):
        self.assertEqual(get_column_label("first_name", {}), "First Name")

    def test_missing_field_uses_title_case(self):
        config = {"other": {"label": "Other"}}
        self.assertEqual(get_column_label("first_name", config), "First Name")


class GetColumnAlignmentTests(DrfCommonTestCase):
    """Tests for get_column_alignment."""

    def test_returns_configured_alignment(self):
        config = {"amount": {"align": "right"}}
        self.assertEqual(get_column_alignment("amount", config), "right")

    def test_defaults_to_left(self):
        self.assertEqual(get_column_alignment("name", {}), "left")

    def test_invalid_alignment_falls_back_to_left(self):
        config = {"name": {"align": "diagonal"}}
        self.assertEqual(get_column_alignment("name", config), "left")

    def test_center_alignment(self):
        config = {"status": {"align": "center"}}
        self.assertEqual(get_column_alignment("status", config), "center")

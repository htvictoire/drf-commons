"""
Tests for ComputedOrderingFilter.
"""

from unittest.mock import Mock, patch

from django.db import models

from drf_commons.common_tests.base_cases import DrfCommonTestCase

from ..computed import ComputedOrderingFilter


class ComputedOrderingFilterTests(DrfCommonTestCase):
    """Tests for ComputedOrderingFilter class."""

    def setUp(self):
        """Set up test dependencies."""
        super().setUp()
        self.filter = ComputedOrderingFilter()

    def create_mock_view(self, computed_fields=None):
        """Create a mock view with computed ordering fields."""
        view = Mock()
        view.computed_ordering_fields = computed_fields or {}
        return view

    def create_mock_request(self, ordering_param=None):
        """Create a mock request with ordering parameter."""
        request = Mock()
        request.query_params = {}
        if ordering_param:
            request.query_params["ordering"] = ordering_param
        return request

    def test_get_valid_fields_without_computed_fields(self):
        """Test get_valid_fields when view has no computed fields."""
        view = self.create_mock_view()
        queryset = Mock()

        with patch("rest_framework.filters.OrderingFilter.get_valid_fields") as mock_super:
            mock_super.return_value = [("name", "name"), ("created_at", "created_at")]

            # Call the actual method
            result = self.filter.get_valid_fields(queryset, view)

            # Should return the same fields as parent
            self.assertEqual(result, [("name", "name"), ("created_at", "created_at")])

    def test_get_valid_fields_with_computed_fields(self):
        """Test get_valid_fields when view has computed fields."""
        computed_fields = {
            "student": ["first_name", "last_name"],
            "class_name": "academic_class__name",
        }
        view = self.create_mock_view(computed_fields)
        queryset = Mock()

        with patch("rest_framework.filters.OrderingFilter.get_valid_fields") as mock_super:
            mock_super.return_value = [("name", "name")]

            # Call the actual method
            result = self.filter.get_valid_fields(queryset, view)

            # Should include computed fields
            expected = [
                ("name", "name"),
                ("student", "student"),
                ("class_name", "class_name"),
            ]
            self.assertEqual(result, expected)

    def test_filter_queryset_no_ordering(self):
        """Test filter_queryset when no ordering is requested."""
        request = self.create_mock_request()
        queryset = Mock()
        view = self.create_mock_view()

        with patch.object(self.filter, "get_ordering", return_value=None):
            with patch("rest_framework.filters.OrderingFilter.filter_queryset") as mock_super:
                mock_super.return_value = queryset

                result = self.filter.filter_queryset(request, queryset, view)

                # Should fall back to parent behavior
                mock_super.assert_called_once_with(request, queryset, view)
                self.assertEqual(result, queryset)

    def test_filter_queryset_no_computed_fields(self):
        """Test filter_queryset when view has no computed fields."""
        request = self.create_mock_request()
        queryset = Mock()
        view = self.create_mock_view()

        with patch.object(
            self.filter, "get_ordering", return_value=["name", "-created_at"]
        ):
            with patch("rest_framework.filters.OrderingFilter.filter_queryset") as mock_super:
                mock_super.return_value = queryset

                result = self.filter.filter_queryset(request, queryset, view)

                # Should fall back to parent behavior
                mock_super.assert_called_once_with(request, queryset, view)
                self.assertEqual(result, queryset)

    def test_filter_queryset_with_string_computed_field(self):
        """Test filter_queryset with string computed field."""
        computed_fields = {"class_name": "academic_class__name"}
        request = self.create_mock_request()
        queryset = Mock()
        view = self.create_mock_view(computed_fields)

        with patch.object(self.filter, "get_ordering", return_value=["class_name"]):
            result = ComputedOrderingFilter.filter_queryset(
                self.filter, request, queryset, view
            )

            # Should apply ordering with computed field lookup
            queryset.order_by.assert_called_once_with("academic_class__name")
            self.assertEqual(result, queryset.order_by.return_value)

    def test_filter_queryset_with_list_computed_field(self):
        """Test filter_queryset with list computed field."""
        computed_fields = {"student": ["first_name", "last_name"]}
        request = self.create_mock_request()
        queryset = Mock()
        view = self.create_mock_view(computed_fields)

        with patch.object(self.filter, "get_ordering", return_value=["-student"]):
            result = ComputedOrderingFilter.filter_queryset(
                self.filter, request, queryset, view
            )

            # Should apply ordering with multiple fields reversed
            queryset.order_by.assert_called_once_with("-first_name", "-last_name")
            self.assertEqual(result, queryset.order_by.return_value)

    def test_filter_queryset_with_aggregate_computed_field(self):
        """Test filter_queryset with aggregate computed field."""
        computed_fields = {"item_count": models.Count("items")}
        request = self.create_mock_request()
        queryset = Mock()
        view = self.create_mock_view(computed_fields)

        with patch.object(self.filter, "get_ordering", return_value=["item_count"]):
            result = ComputedOrderingFilter.filter_queryset(
                self.filter, request, queryset, view
            )

            # Should apply annotation and then ordering
            queryset.annotate.assert_called_once()
            annotated_queryset = queryset.annotate.return_value
            annotated_queryset.order_by.assert_called_once_with("item_count_order")
            self.assertEqual(result, annotated_queryset.order_by.return_value)

    def test_filter_queryset_mixed_fields(self):
        """Test filter_queryset with mix of regular and computed fields."""
        computed_fields = {
            "student": ["first_name", "last_name"],
            "class_name": "academic_class__name",
        }
        request = self.create_mock_request()
        queryset = Mock()
        view = self.create_mock_view(computed_fields)

        with patch.object(
            self.filter, "get_ordering", return_value=["name", "-student", "class_name"]
        ):
            result = ComputedOrderingFilter.filter_queryset(
                self.filter, request, queryset, view
            )

            # Should apply ordering with mixed fields
            expected_ordering = [
                "name",
                "-first_name",
                "-last_name",
                "academic_class__name",
            ]
            queryset.order_by.assert_called_once_with(*expected_ordering)
            self.assertEqual(result, queryset.order_by.return_value)

    def test_filter_queryset_no_processed_ordering(self):
        """Test filter_queryset when processed ordering is empty."""
        computed_fields = {"test_field": "related__name"}
        request = self.create_mock_request()
        queryset = Mock()
        view = self.create_mock_view(computed_fields)

        with patch.object(self.filter, "get_ordering", return_value=["other_field"]):
            with patch(
                "drf_commons.filters.ordering.processors.process_ordering", return_value=([], {})
            ):
                result = self.filter.filter_queryset(request, queryset, view)

                # Should fall back to parent behavior, which applies the original ordering
                # The parent OrderingFilter should process the original ordering ["other_field"]
                queryset.order_by.assert_called_once_with("other_field")
                self.assertEqual(result, queryset.order_by.return_value)

    def test_filter_queryset_empty_ordering(self):
        """Test filter_queryset when ordering list is empty."""
        computed_fields = {"test_field": "related__name"}
        request = self.create_mock_request()
        queryset = Mock()
        view = self.create_mock_view(computed_fields)

        with patch.object(self.filter, "get_ordering", return_value=[]):
            with patch("rest_framework.filters.OrderingFilter.filter_queryset") as mock_super:
                mock_super.return_value = queryset

                result = self.filter.filter_queryset(request, queryset, view)

                # Should fall back to parent behavior
                mock_super.assert_called_once_with(request, queryset, view)
                self.assertEqual(result, queryset)

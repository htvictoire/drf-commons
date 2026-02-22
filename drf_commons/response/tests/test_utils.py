"""
Tests for response utility functions.
"""

from rest_framework import status
from rest_framework.response import Response

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from ..utils import error_response, success_response


class SuccessResponseTestCase(DrfCommonTestCase):
    """Test success_response function."""

    def test_success_response_basic(self):
        """Test basic success response."""
        response = success_response()

        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("timestamp", response.data)

    def test_success_response_with_data_dict(self):
        """Test success response with dict data."""
        data = {"users": [{"id": 1, "name": "Test User"}]}
        response = success_response(data=data)

        self.assertEqual(response.data["data"], data)
        self.assertTrue(response.data["success"])

    def test_success_response_with_data_list(self):
        """Test success response with list data."""
        data = [{"id": 1, "name": "Test User"}]
        response = success_response(data=data)

        self.assertEqual(response.data["data"], {"results": data})
        self.assertTrue(response.data["success"])

    def test_success_response_with_message(self):
        """Test success response with message."""
        message = "Operation completed successfully"
        response = success_response(message=message)

        self.assertEqual(response.data["message"], message)
        self.assertTrue(response.data["success"])

    def test_success_response_with_custom_status(self):
        """Test success response with custom status code."""
        response = success_response(status_code=status.HTTP_201_CREATED)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

    def test_success_response_with_headers(self):
        """Test success response with custom headers."""
        headers = {"X-Custom-Header": "test-value"}
        response = success_response(headers=headers)

        self.assertEqual(response["X-Custom-Header"], "test-value")

    def test_success_response_with_kwargs(self):
        """Test success response with additional kwargs."""
        response = success_response(custom_field="custom_value")

        self.assertEqual(response.data["data"]["custom_field"], "custom_value")
        self.assertTrue(response.data["success"])


class ErrorResponseTestCase(DrfCommonTestCase):
    """Test error_response function."""

    def test_error_response_basic(self):
        """Test basic error response."""
        response = error_response()

        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "An error occurred")
        self.assertIn("timestamp", response.data)

    def test_error_response_with_message(self):
        """Test error response with custom message."""
        message = "Custom error message"
        response = error_response(message=message)

        self.assertEqual(response.data["message"], message)
        self.assertFalse(response.data["success"])

    def test_error_response_with_custom_status(self):
        """Test error response with custom status code."""
        response = error_response(status_code=status.HTTP_404_NOT_FOUND)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["success"])

    def test_error_response_with_errors(self):
        """Test error response with detailed errors."""
        errors = {"field1": ["This field is required"], "field2": ["Invalid value"]}
        response = error_response(errors=errors)

        self.assertEqual(response.data["errors"], errors)
        self.assertFalse(response.data["success"])

    def test_error_response_with_kwargs(self):
        """Test error response with additional kwargs."""
        response = error_response(custom_field="custom_value")

        self.assertEqual(response.data["data"]["custom_field"], "custom_value")
        self.assertFalse(response.data["success"])

"""
Tests for exception classes.

Tests custom exception classes used in import operations.
"""

from drf_common.common_tests.base_cases import DrfCommonTestCase

from ..exceptions import ImportErrorRow, ImportValidationError


class ExceptionsTests(DrfCommonTestCase):
    """Tests for import exception classes."""

    def test_import_error_row_basic_initialization(self):
        """Test ImportErrorRow initializes with message."""
        error = ImportErrorRow("Test error message")
        self.assertEqual(str(error), "Test error message")
        self.assertIsNone(error.row_number)
        self.assertIsNone(error.field_name)

    def test_import_error_row_with_row_number(self):
        """Test ImportErrorRow with row number."""
        error = ImportErrorRow("Test error", row_number=5)
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.row_number, 5)
        self.assertIsNone(error.field_name)

    def test_import_error_row_with_field_name(self):
        """Test ImportErrorRow with field name."""
        error = ImportErrorRow("Test error", field_name="username")
        self.assertEqual(str(error), "Test error")
        self.assertIsNone(error.row_number)
        self.assertEqual(error.field_name, "username")

    def test_import_error_row_with_all_parameters(self):
        """Test ImportErrorRow with all parameters."""
        error = ImportErrorRow("Test error", row_number=5, field_name="username")
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.row_number, 5)
        self.assertEqual(error.field_name, "username")

    def test_import_error_row_is_exception(self):
        """Test ImportErrorRow inherits from Exception."""
        error = ImportErrorRow("Test error")
        self.assertIsInstance(error, Exception)

    def test_import_validation_error_basic_initialization(self):
        """Test ImportValidationError initializes with message."""
        error = ImportValidationError("Validation failed")
        self.assertEqual(str(error), "Validation failed")

    def test_import_validation_error_is_exception(self):
        """Test ImportValidationError inherits from Exception."""
        error = ImportValidationError("Validation failed")
        self.assertIsInstance(error, Exception)

    def test_import_error_row_can_be_raised(self):
        """Test ImportErrorRow can be raised and caught."""
        with self.assertRaises(ImportErrorRow) as cm:
            raise ImportErrorRow("Test error", row_number=10, field_name="email")

        error = cm.exception
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.row_number, 10)
        self.assertEqual(error.field_name, "email")

    def test_import_validation_error_can_be_raised(self):
        """Test ImportValidationError can be raised and caught."""
        with self.assertRaises(ImportValidationError) as cm:
            raise ImportValidationError("Configuration is invalid")

        error = cm.exception
        self.assertEqual(str(error), "Configuration is invalid")

"""
Tests for configuration enums.

Tests enum definitions used in import configuration.
"""

from drf_commons.common_tests.base_cases import DrfCommonTestCase

from ..enums import FileFormat


class EnumsTests(DrfCommonTestCase):
    """Tests for configuration enums."""

    def test_file_format_enum_values(self):
        """Test FileFormat enum has correct values."""
        self.assertEqual(FileFormat.CSV.value, "csv")
        self.assertEqual(FileFormat.XLSX.value, "xlsx")
        self.assertEqual(FileFormat.XLS.value, "xls")

    def test_file_format_enum_members(self):
        """Test FileFormat enum has correct members."""
        expected_members = {"CSV", "XLSX", "XLS"}
        actual_members = {member.name for member in FileFormat}
        self.assertEqual(actual_members, expected_members)

    def test_file_format_enum_access(self):
        """Test FileFormat enum members can be accessed."""
        self.assertEqual(FileFormat["CSV"], FileFormat.CSV)
        self.assertEqual(FileFormat["XLSX"], FileFormat.XLSX)
        self.assertEqual(FileFormat["XLS"], FileFormat.XLS)

    def test_file_format_string_representation(self):
        """Test FileFormat enum string representation."""
        self.assertEqual(str(FileFormat.CSV), "FileFormat.CSV")
        self.assertEqual(str(FileFormat.XLSX), "FileFormat.XLSX")
        self.assertEqual(str(FileFormat.XLS), "FileFormat.XLS")

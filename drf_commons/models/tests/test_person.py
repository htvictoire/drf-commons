"""
Tests for person-related models and mixins.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from drf_commons.common_tests.base_cases import ModelTestCase

from ..person import AddressMixin, PersonMixin, IdentityMixin

User = get_user_model()


class IdentityModelForTesting(IdentityMixin):
    """Test model using IdentityMixin."""

    class Meta:
        app_label = "drf_commons"


class AddressModelForTesting(AddressMixin):
    """Test model using AddressMixin."""

    class Meta:
        app_label = "drf_commons"

    name = models.CharField(max_length=100)


class PersonMixinModelForTesting(PersonMixin):
    """Test model using PersonMixin."""

    class Meta:
        app_label = "drf_commons"


class IdentityMixinTests(ModelTestCase):
    """Tests for IdentityMixin."""

    def test_full_name_with_all_names(self):
        """Test full_name property with all names."""
        model = IdentityModelForTesting(
            first_name="John", middle_name="Edward", last_name="Doe"
        )

        self.assertEqual(model.full_name, "John Edward Doe")

    def test_full_name_without_middle_name(self):
        """Test full_name property without middle name."""
        model = IdentityModelForTesting(first_name="John", last_name="Doe")

        self.assertEqual(model.full_name, "John Doe")

    def test_full_name_without_last_name(self):
        """Test full_name property without last name."""
        model = IdentityModelForTesting(first_name="John")

        self.assertEqual(model.full_name, "John")

    def test_initials_with_all_names(self):
        """Test initials property with all names."""
        model = IdentityModelForTesting(
            first_name="John", middle_name="Edward", last_name="Doe"
        )

        self.assertEqual(model.initials, "JED")

    def test_initials_without_middle_name(self):
        """Test initials property without middle name."""
        model = IdentityModelForTesting(first_name="John", last_name="Doe")

        self.assertEqual(model.initials, "JD")

    def test_initials_case_handling(self):
        """Test initials property handles case correctly."""
        model = IdentityModelForTesting(
            first_name="john", middle_name="edward", last_name="doe"
        )

        self.assertEqual(model.initials, "JED")

    def test_age_calculation(self):
        """Test age property calculates correctly."""
        birth_date = date(1990, 5, 15)
        model = IdentityModelForTesting(date_of_birth=birth_date)

        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value.date.return_value = date(2023, 8, 20)

            age = model.age

            self.assertEqual(age, 33)

    def test_age_birthday_not_yet_this_year(self):
        """Test age property when birthday hasn't occurred this year."""
        birth_date = date(1990, 10, 15)
        model = IdentityModelForTesting(date_of_birth=birth_date)

        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value.date.return_value = date(2023, 5, 20)

            age = model.age

            self.assertEqual(age, 32)

    def test_age_birthday_today(self):
        """Test age property when today is birthday."""
        birth_date = date(1990, 5, 15)
        model = IdentityModelForTesting(date_of_birth=birth_date)

        with patch("django.utils.timezone.now") as mock_now:
            mock_now.return_value.date.return_value = date(2023, 5, 15)

            age = model.age

            self.assertEqual(age, 33)

    def test_age_without_date_of_birth(self):
        """Test age property returns None without date of birth."""
        model = IdentityModelForTesting()

        self.assertIsNone(model.age)

    def test_str_representation(self):
        """Test string representation."""
        model = IdentityModelForTesting(first_name="John", last_name="Doe")

        self.assertEqual(str(model), "John Doe")


class AddressMixinTests(ModelTestCase):
    """Tests for AddressMixin."""

    def test_full_address_all_fields(self):
        """Test full_address property with all fields."""
        model = AddressModelForTesting(
            street_address="123 Main St",
            street_address_2="Apt 4B",
            city="New York",
            state_province="NY",
            postal_code="10001",
            country="USA",
        )

        expected = "123 Main St, Apt 4B, New York, NY, 10001, USA"
        self.assertEqual(model.full_address, expected)

    def test_full_address_partial_fields(self):
        """Test full_address property with partial fields."""
        model = AddressModelForTesting(
            street_address="123 Main St", city="New York", country="USA"
        )

        expected = "123 Main St, New York, USA"
        self.assertEqual(model.full_address, expected)

    def test_full_address_empty_fields(self):
        """Test full_address property with empty fields."""
        model = AddressModelForTesting()

        self.assertEqual(model.full_address, "")

    def test_short_address(self):
        """Test short_address property."""
        model = AddressModelForTesting(
            street_address="123 Main St",
            city="New York",
            state_province="NY",
            country="USA",
        )

        expected = "New York, NY, USA"
        self.assertEqual(model.short_address, expected)

    def test_has_coordinates_true(self):
        """Test has_coordinates property returns True when both coordinates set."""
        model = AddressModelForTesting(
            latitude=Decimal("40.7128"), longitude=Decimal("-74.0060")
        )

        self.assertTrue(model.has_coordinates)

    def test_has_coordinates_false(self):
        """Test has_coordinates property returns False when coordinates missing."""
        model = AddressModelForTesting(longitude=Decimal("-74.0060"))

        self.assertFalse(model.has_coordinates)

    def test_get_coordinates_with_coordinates(self):
        """Test get_coordinates returns tuple when coordinates set."""
        model = AddressModelForTesting(
            latitude=Decimal("40.7128"), longitude=Decimal("-74.0060")
        )

        coordinates = model.get_coordinates()

        self.assertEqual(coordinates, (40.7128, -74.0060))

    def test_get_coordinates_without_coordinates(self):
        """Test get_coordinates returns None when coordinates not set."""
        model = AddressModelForTesting()

        coordinates = model.get_coordinates()

        self.assertIsNone(coordinates)


class PersonMixinTests(ModelTestCase):
    """Tests for PersonMixin model."""

    def test_get_display_info(self):
        """Test get_display_info returns correct information."""
        model = PersonMixinModelForTesting(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="123-456-7890",
            city="New York",
            country="USA",
        )
        model.created_at = timezone.now()

        display_info = model.get_display_info()

        self.assertEqual(display_info["full_name"], "John Doe")
        self.assertEqual(display_info["email"], "john.doe@example.com")
        self.assertEqual(display_info["phone"], "123-456-7890")
        self.assertEqual(display_info["short_address"], "New York, USA")
        self.assertIn("id", display_info)
        self.assertIn("created_at", display_info)

    def test_get_contact_info_filters_empty_values(self):
        """Test get_contact_info filters out empty values."""
        model = PersonMixinModelForTesting(
            email="john.doe@example.com",
            phone="",
        )

        contact_info = model.get_contact_info()

        self.assertEqual(contact_info["email"], "john.doe@example.com")
        self.assertNotIn("phone", contact_info)

    def test_str_representation(self):
        """Test string representation includes name and email."""
        model = PersonMixinModelForTesting(
            first_name="John", last_name="Doe", email="john.doe@example.com"
        )

        expected = "John Doe (john.doe@example.com)"
        self.assertEqual(str(model), expected)

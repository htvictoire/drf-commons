"""
Person-related mixins and models.

This module contains mixins and models specifically designed for
representing people and their associated information like identity
and address details.
"""

from typing import Any, Dict, Optional

from django.db import models
from django.utils import timezone

from .base import AbstractBaseModel


class IdentityMixin(models.Model):
    """
    Mixin that provides personal identity fields.

    Contains common personal information fields used across different models
    that represent people or entities with personal details.

    Attributes:
        first_name: Person's first name
        last_name: Person's last name
        middle_name: Person's middle name (optional)
        email: Person's email address
        phone: Person's phone number
        date_of_birth: Person's date of birth
        gender: Person's gender
        nationality: Person's nationality
    """

    class GenderChoices(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"

    first_name = models.CharField(max_length=100, help_text="Person's first name")
    last_name = models.CharField(
        max_length=100, blank=True, null=True, help_text="Person's last name"
    )
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Person's middle name (optional)",
    )
    email = models.EmailField(unique=True, help_text="Person's email address")
    phone = models.CharField(
        max_length=20, blank=True, null=True, help_text="Person's phone number"
    )
    date_of_birth = models.DateField(
        null=True, blank=True, help_text="Person's date of birth"
    )
    birth_place = models.TextField(
        blank=True, null=True, help_text="Person's birth place full address"
    )
    gender = models.CharField(
        max_length=20,
        choices=GenderChoices.choices,
        blank=True,
        null=True,
        help_text="Person's gender",
    )
    nationality = models.CharField(
        max_length=100, blank=True, null=True, help_text="Person's nationality"
    )

    class Meta:
        abstract = True

    @property
    def full_name(self) -> str:
        """
        Get the person's full name.

        Returns:
            Full name combining first, middle (if exists), and last name
        """
        names = [self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        if self.last_name:
            names.append(self.last_name)
        return " ".join(names)

    @property
    def initials(self) -> str:
        """
        Get the person's initials.

        Returns:
            Initials from first, middle (if exists), and last name
        """
        initials = [self.first_name[0].upper()]
        if self.middle_name:
            initials.append(self.middle_name[0].upper())
        if self.last_name:
            initials.append(self.last_name[0].upper())
        return "".join(initials)

    @property
    def age(self) -> Optional[int]:
        """
        Calculate the person's age based on date of birth.

        Returns:
            Age in years, or None if date_of_birth is not set
        """
        if not self.date_of_birth:
            return None

        today = timezone.now().date()
        age = today.year - self.date_of_birth.year

        # Adjust if birthday hasn't occurred this year
        if today.month < self.date_of_birth.month or (
            today.month == self.date_of_birth.month
            and today.day < self.date_of_birth.day
        ):
            age -= 1

        return age

    def __str__(self) -> str:
        """String representation of the person."""
        return self.full_name


class AddressMixin(models.Model):
    """
    Mixin that provides address fields.

    Contains address information fields that can be used
    across different models that need location/address data.

    Attributes:
        street_address: Street address line 1
        street_address_2: Street address line 2 (apartment, suite, etc.)
        city: City name
        state_province: State or province
        postal_code: ZIP/postal code
        country: Country name
        latitude: Geographic latitude coordinate
        longitude: Geographic longitude coordinate
    """

    street_address = models.CharField(
        max_length=255, blank=True, null=True, help_text="Street address line 1"
    )
    street_address_2 = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Street address line 2 (apartment, suite, etc.)",
    )
    city = models.CharField(
        max_length=100, blank=True, null=True, help_text="City name"
    )
    state_province = models.CharField(
        max_length=100, blank=True, null=True, help_text="State or province"
    )
    postal_code = models.CharField(
        max_length=20, blank=True, null=True, help_text="ZIP/postal code"
    )
    country = models.CharField(
        max_length=100, blank=True, null=True, help_text="Country name"
    )
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Geographic latitude coordinate",
    )
    longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Geographic longitude coordinate",
    )

    class Meta:
        abstract = True

    @property
    def full_address(self) -> str:
        """
        Get the complete formatted address.

        Returns:
            Full address string with all non-empty fields
        """
        address_parts = []

        if self.street_address:
            address_parts.append(self.street_address)
        if self.street_address_2:
            address_parts.append(self.street_address_2)
        if self.city:
            address_parts.append(self.city)
        if self.state_province:
            address_parts.append(self.state_province)
        if self.postal_code:
            address_parts.append(self.postal_code)
        if self.country:
            address_parts.append(self.country)

        return ", ".join(address_parts)

    @property
    def short_address(self) -> str:
        """
        Get a shortened version of the address.

        Returns:
            Short address with city, state, and country
        """
        address_parts = []

        if self.city:
            address_parts.append(self.city)
        if self.state_province:
            address_parts.append(self.state_province)
        if self.country:
            address_parts.append(self.country)

        return ", ".join(address_parts)

    @property
    def has_coordinates(self) -> bool:
        """
        Check if the address has geographic coordinates.

        Returns:
            True if both latitude and longitude are set
        """
        return self.latitude is not None and self.longitude is not None

    def get_coordinates(self) -> Optional[tuple]:
        """
        Get the geographic coordinates as a tuple.

        Returns:
            Tuple of (latitude, longitude) or None if coordinates not set
        """
        if self.has_coordinates:
            return (float(self.latitude), float(self.longitude))
        return None


class BasePerson(AbstractBaseModel, IdentityMixin, AddressMixin):
    """
    Base person model that combines identity and address information.

    This model provides a complete foundation for any person-related models
    in the system, combining personal identity information with address data,
    along with standard tracking fields from AbstractBaseModel.

    Inherits from:
        - AbstractBaseModel: Provides UUID, timestamps, user tracking, JSON serialization
        - IdentityMixin: Provides personal identity fields (name, email, phone, etc.)
        - AddressMixin: Provides address fields

    This model can be used as a base for:
        - Customer models
        - Employee models
        - Contact models
        - User profile models
        - Any other person-related entities
    """

    class Meta(AbstractBaseModel.Meta):
        abstract = True

    def get_display_info(self) -> Dict[str, Any]:
        """
        Get a dictionary of key display information for the person.

        Returns:
            Dictionary containing key person information for display purposes
        """
        return {
            "id": str(self.id),
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "short_address": self.short_address,
            "age": self.age,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def get_contact_info(self) -> Dict[str, str]:
        """
        Get contact information for the person.

        Returns:
            Dictionary containing contact information
        """
        contact_info = {
            "email": self.email,
            "phone": self.phone,
        }

        if self.full_address:
            contact_info["address"] = self.full_address

        return {k: v for k, v in contact_info.items() if v}

    def __str__(self) -> str:
        """String representation of the person."""
        return f"{self.full_name} ({self.email})"

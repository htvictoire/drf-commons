"""
Common models package.

This package provides reusable mixins and base models for Django applications.
It's organized into logical modules for better maintainability and easier imports.

Modules:
    base: Core mixins (UserActionMixin, TimeStampMixin, SoftDeleteMixin, BaseModelMixin)
    content: Content-related mixins (SlugMixin, MetaMixin, VersionMixin)
    person: Person-related mixins and models (IdentityMixin, AddressMixin, PersonMixin)

Usage:
    from drf_commons.models import BaseModelMixin, PersonMixin
    from drf_commons.models import UserActionMixin, TimeStampMixin
    from drf_commons.models import IdentityMixin, AddressMixin
    from drf_commons.models import SlugMixin, MetaMixin, VersionMixin
"""

# Base mixins and models
from .base import (
    BaseModelMixin,
    SoftDeleteMixin,
    TimeStampMixin,
    UserActionMixin,
)

# Content-related mixins
from .content import (
    MetaMixin,
    SlugMixin,
    VersionMixin,
)

# Custom fields
from .fields import (
    CurrentUserField,
)

# Person-related mixins and models
from .person import (
    AddressMixin,
    PersonMixin,
    IdentityMixin,
)

__all__ = [
    # Base mixins and models
    "BaseModelMixin",
    "UserActionMixin",
    "TimeStampMixin",
    "SoftDeleteMixin",
    # Content mixins
    "SlugMixin",
    "MetaMixin",
    "VersionMixin",
    # Person mixins and models
    "IdentityMixin",
    "AddressMixin",
    "PersonMixin",
    # Custom fields
    "CurrentUserField",
]

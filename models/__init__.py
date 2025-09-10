"""
Common models package.

This package provides reusable mixins and base models for Django applications.
It's organized into logical modules for better maintainability and easier imports.

Modules:
    base: Core mixins (UserActionMixin, TimeStampMixin, SoftDeleteMixin, AbstractBaseModel)
    content: Content-related mixins (SlugMixin, MetaMixin, VersionMixin)
    person: Person-related mixins and models (IdentityMixin, AddressMixin, BasePerson)

Usage:
    from common.models import AbstractBaseModel, BasePerson
    from common.models import UserActionMixin, TimeStampMixin
    from common.models import IdentityMixin, AddressMixin
    from common.models import SlugMixin, MetaMixin, VersionMixin
"""

# Base mixins and models
from .base import (
    AbstractBaseModel,
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

# Person-related mixins and models
from .person import (
    AddressMixin,
    BasePerson,
    IdentityMixin,
)

__all__ = [
    # Base mixins and models
    'AbstractBaseModel',
    'UserActionMixin',
    'TimeStampMixin',
    'SoftDeleteMixin',
    
    # Content mixins
    'SlugMixin',
    'MetaMixin',
    'VersionMixin',
    
    # Person mixins and models
    'IdentityMixin',
    'AddressMixin',
    'BasePerson',
]
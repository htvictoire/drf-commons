"""
DRF Commons - Django REST Framework Common Utilities

This package provides common utilities and extensions for Django REST Framework.
Register only the umbrella application in ``INSTALLED_APPS``.

Usage:
    INSTALLED_APPS = [
        'drf_commons',
    ]
"""

from importlib.metadata import version

__version__ = version("drf-commons")
__author__ = "Victoire HABAMUNGU"

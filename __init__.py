"""
DRF Commons - Django REST Framework Common Utilities

This package provides common utilities and extensions for Django REST Framework.
It can be used as a complete package or individual sub-applications.

Usage:
    # Use complete package (includes all sub-apps)
    INSTALLED_APPS = ['drf_commons']

    # Use individual sub-apps
    INSTALLED_APPS = [
        'drf_commons.current_user',
        'drf_commons.filters',
        'drf_commons.pagination',
        # ... etc
    ]
"""

__version__ = "1.0.0"
__author__ = "Victoire HABAMUNGU"

default_app_config = "drf_commons.apps.DrfCommonConfig"

"""
DRF Common - Django REST Framework Common Utilities

This package provides common utilities and extensions for Django REST Framework.
It can be used as a complete package or individual sub-applications.

Usage:
    # Use complete package (includes all sub-apps)
    INSTALLED_APPS = ['drf_common']
    
    # Use individual sub-apps
    INSTALLED_APPS = [
        'drf_common.current_user',
        'drf_common.filters',
        'drf_common.pagination',
        # ... etc
    ]
"""

__version__ = "1.0.0"
__author__ = "Victoire HABAMUNGU"

default_app_config = "drf_common.apps.DrfCommonConfig"
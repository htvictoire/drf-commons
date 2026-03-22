"""
DRF Commons - Django REST Framework utilities and base classes.

Provides composable mixins, standardised responses, bulk operations,
import/export services, and async-safe current user propagation for
Django REST Framework projects.

Register the umbrella application in ``INSTALLED_APPS``:

    INSTALLED_APPS = [
        'drf_commons',
    ]
"""

from importlib.metadata import version

__version__ = version("drf-commons")
__author__ = "Victoire HABAMUNGU"
__email__ = "contact@htvictoire.me"

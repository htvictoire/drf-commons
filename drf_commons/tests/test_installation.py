"""
Installation and import tests for library components.

Tests library can be installed and imported correctly.
"""

import importlib
import sys
from unittest.mock import patch

from django.test import TestCase


class LibraryInstallationTests(TestCase):
    """Test library can be installed and imported correctly."""

    def test_main_package_importable(self):
        """Test main drf_commons package can be imported."""
        try:
            import drf_commons
            self.assertTrue(hasattr(drf_commons, '__version__'))
        except ImportError:
            self.fail("drf_commons package could not be imported")

    def test_all_public_modules_importable(self):
        """Test all documented public modules can be imported."""
        public_modules = [
            'drf_commons.current_user',
            'drf_commons.debug',
            'drf_commons.decorators',
            'drf_commons.filters',
            'drf_commons.middlewares',
            'drf_commons.models',
            'drf_commons.pagination',
            'drf_commons.response',
            'drf_commons.serializers',
            'drf_commons.services',
            'drf_commons.views',
            'drf_commons.templatetags',
            'drf_commons.utils',
        ]

        for module_name in public_modules:
            with self.subTest(module=module_name):
                try:
                    importlib.import_module(module_name)
                except ImportError as e:
                    self.fail(f"Could not import {module_name}: {e}")

    def test_public_api_imports(self):
        """Test main public API classes can be imported."""
        api_imports = [
            # Views
            ('drf_commons.views.base', 'BaseViewSet'),
            ('drf_commons.views.mixins', 'BulkCreateModelMixin'),
            ('drf_commons.views.mixins', 'FileImportMixin'),

            # Serializers
            ('drf_commons.serializers.fields.custom', 'FlexibleField'),

            # Models
            ('drf_commons.models.base', 'BaseModelMixin'),

            # Services
            ('drf_commons.services.import_from_file.service', 'FileImportService'),
            ('drf_commons.services.export_file.service', 'ExportService'),

            # Middlewares
            ('drf_commons.middlewares.current_user', 'CurrentUserMiddleware'),
            ('drf_commons.middlewares.debug', 'DebugMiddleware'),
        ]

        for module_name, class_name in api_imports:
            with self.subTest(module=module_name, cls=class_name):
                try:
                    module = importlib.import_module(module_name)
                    self.assertTrue(
                        hasattr(module, class_name),
                        f"{class_name} not found in {module_name}"
                    )
                except ImportError as e:
                    self.fail(f"Could not import {module_name}: {e}")

    def test_optional_dependencies_handling(self):
        """Test library works with and without optional dependencies."""
        # Test import without openpyxl
        with patch.dict(sys.modules, {'openpyxl': None}):
            try:
                importlib.import_module(
                    "drf_commons.services.export_file.exporters.xlsx_exporter"
                )
                # Should not fail during import, only during usage
            except ImportError:
                self.fail("xlsx_exporter should import even without openpyxl")

        # Test import without reportlab
        with patch.dict(sys.modules, {'reportlab': None}):
            try:
                importlib.import_module(
                    "drf_commons.services.export_file.exporters.pdf_exporter"
                )
                # Should not fail during import, only during usage
            except ImportError:
                self.fail("pdf_exporter should import even without reportlab")

    def test_django_app_configuration(self):
        """Test Django apps are properly configured."""
        from django.apps import apps

        app_config = apps.get_app_config("drf_commons")
        self.assertEqual(app_config.name, "drf_commons")

    def test_settings_module_exists(self):
        """Test settings modules can be imported."""
        try:
            from drf_commons.common_conf import settings
            self.assertTrue(hasattr(settings, 'IMPORT_BATCH_SIZE'))
        except ImportError:
            self.fail("Could not import drf_commons settings")

        try:
            importlib.import_module(
                "drf_commons.common_conf.django_settings"
            )
            # Should import without error
        except ImportError:
            self.fail("Could not import django_settings")

    def test_management_command_discovery(self):
        """Test commands are discoverable with umbrella app registration."""
        from django.core.management import get_commands

        commands = get_commands()
        self.assertIn("generate_import_template", commands)

    def test_common_tests_utilities_importable(self):
        """Test common test utilities can be imported."""
        test_utilities = [
            'drf_commons.common_tests.base_cases',
            'drf_commons.common_tests.factories',
            'drf_commons.common_tests.utils',
            'drf_commons.common_tests.serializers',
        ]

        for util_module in test_utilities:
            with self.subTest(util=util_module):
                try:
                    importlib.import_module(util_module)
                except ImportError as e:
                    self.fail(f"Could not import test utility {util_module}: {e}")


class ModularUsageTests(TestCase):
    """Test library components can be used independently."""

    def test_current_user_standalone(self):
        """Test current_user module works independently."""
        from drf_commons.current_user.utils import get_current_user

        # Should start with no current user
        self.assertIsNone(get_current_user())

    def test_decorators_standalone(self):
        """Test decorators work without other modules."""
        from drf_commons.decorators.cache import cache_debug

        @cache_debug()
        def cached_function(x):
            return x * 2

        # Function should be callable
        self.assertEqual(cached_function(5), 10)

    def test_response_utils_standalone(self):
        """Test response utilities work independently."""
        from drf_commons.response.utils import success_response, error_response

        success = success_response(data={"id": 1}, message="Operation successful")
        self.assertEqual(success.status_code, 200)

        error = error_response(message="Operation failed", error_code="INVALID")
        self.assertEqual(error.status_code, 400)

    def test_models_standalone(self):
        """Test model mixins work independently."""
        from django.db import models
        from drf_commons.models.mixins import TimeStampMixin

        # Create a test model using the mixin
        class TestModel(TimeStampMixin, models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = 'test'

        # Verify mixin fields exist
        field_names = [field.name for field in TestModel._meta.fields]
        self.assertIn('created_at', field_names)
        self.assertIn('updated_at', field_names)

    def test_templatetags_standalone(self):
        """Test template tags work independently."""
        from drf_commons.templatetags.dict_extras import get_item

        test_dict = {"key1": "value1", "nested": {"key2": "value2"}}

        self.assertEqual(get_item(test_dict, "key1"), "value1")
        self.assertEqual(get_item(test_dict, "missing"), "")


class CompatibilityTests(TestCase):
    """Test compatibility with different Django/DRF versions."""

    def test_django_version_compatibility(self):
        """Test library works with supported Django versions."""
        import django

        # Check minimum Django version
        django_version = django.VERSION
        self.assertGreaterEqual(
            django_version[:2], (3, 2),
            "Django 3.2+ is required"
        )

    def test_drf_version_compatibility(self):
        """Test library works with supported DRF versions."""
        import rest_framework

        # Check minimum DRF version
        drf_version = tuple(map(int, rest_framework.VERSION.split('.')))
        self.assertGreaterEqual(
            drf_version[:2], (3, 12),
            "Django REST Framework 3.12+ is required"
        )

    def test_python_version_compatibility(self):
        """Test library works with supported Python versions."""
        import sys

        # Check minimum Python version
        python_version = sys.version_info
        self.assertGreaterEqual(
            python_version[:2], (3, 8),
            "Python 3.8+ is required"
        )

    def test_import_with_minimal_django_settings(self):
        """Test library imports work with minimal Django configuration."""
        # This test verifies imports don't fail due to missing Django settings
        # The actual Django setup is handled by the test framework

        required_modules = [
            'drf_commons.models.base',
            'drf_commons.serializers.fields.base',
            'drf_commons.views.base',
        ]

        for module_name in required_modules:
            with self.subTest(module=module_name):
                try:
                    importlib.import_module(module_name)
                except Exception as e:
                    # Should not fail due to Django configuration issues
                    if "django.core.exceptions.ImproperlyConfigured" in str(type(e)):
                        self.fail(f"Module {module_name} failed due to Django config: {e}")

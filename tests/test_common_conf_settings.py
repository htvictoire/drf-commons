from django.test import override_settings

from drf_commons.common_tests.base_cases import DrfCommonTestCase
from drf_commons.common_conf import settings as common_settings
from drf_commons.common_conf.settings import CommonSettings, get_setting


class CommonSettingsTests(DrfCommonTestCase):
    @override_settings(COMMON_IMPORT_BATCH_SIZE=321, IMPORT_BATCH_SIZE=123)
    def test_common_settings_prefers_namespaced_override(self):
        settings_obj = CommonSettings()

        self.assertEqual(settings_obj.get("IMPORT_BATCH_SIZE"), 321)

    @override_settings(DEBUG_SQL_BORDER_LENGTH=99)
    def test_common_settings_falls_back_to_plain_django_setting(self):
        settings_obj = CommonSettings()

        self.assertEqual(settings_obj.get("DEBUG_SQL_BORDER_LENGTH"), 99)

    def test_common_settings_returns_default_for_missing_key(self):
        settings_obj = CommonSettings()

        self.assertEqual(settings_obj.get("NOT_DEFINED", "fallback"), "fallback")

    def test_common_settings_attribute_access_and_module_access(self):
        with override_settings(COMMON_DEBUG_LOGS_BASE_DIR="runtime-logs"):
            self.assertEqual(common_settings.DEBUG_LOGS_BASE_DIR, "runtime-logs")
            self.assertEqual(get_setting("DEBUG_LOGS_BASE_DIR"), "runtime-logs")
            self.assertEqual(
                common_settings.IMPORT_BATCH_SIZE,
                common_settings.DEFAULT_SETTINGS["IMPORT_BATCH_SIZE"],
            )

    def test_common_settings_raise_for_unknown_attributes(self):
        settings_obj = CommonSettings()

        with self.assertRaises(AttributeError):
            _ = settings_obj.UNKNOWN_SETTING

        with self.assertRaises(AttributeError):
            _ = common_settings.UNKNOWN_SETTING

    def test_get_setting_uses_passed_default_for_unknown_keys(self):
        self.assertEqual(get_setting("MISSING_SETTING", "custom-default"), "custom-default")

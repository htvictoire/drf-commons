from django.apps import AppConfig


class DebugConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_common.debug"
    label = "drf_common_debug"
    verbose_name = "DRF Common - Debug Tools"
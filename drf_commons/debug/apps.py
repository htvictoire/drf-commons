from django.apps import AppConfig


class DebugConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_commons.debug"
    label = "drf_commons_debug"
    verbose_name = "DRF Commons - Debug Tools"

from django.apps import AppConfig


class CurrentUserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_common.current_user"
    label = "drf_common_current_user"
    verbose_name = "DRF Common - Current User"
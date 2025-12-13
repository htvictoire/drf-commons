from django.apps import AppConfig


class CurrentUserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_commons.current_user"
    label = "drf_commons_current_user"
    verbose_name = "DRF Commons - Current User"

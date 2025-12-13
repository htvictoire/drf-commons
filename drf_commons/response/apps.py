from django.apps import AppConfig


class ResponseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_commons.response"
    label = "drf_commons_response"
    verbose_name = "DRF Commons - Response Utilities"

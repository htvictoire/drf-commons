from django.apps import AppConfig


class ResponseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_common.response"
    label = "drf_common_response"
    verbose_name = "DRF Common - Response Utilities"

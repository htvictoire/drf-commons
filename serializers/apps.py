from django.apps import AppConfig


class SerializersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_common.serializers"
    label = "drf_common_serializers"
    verbose_name = "DRF Common - Serializers"
from django.apps import AppConfig


class SerializersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_commons.serializers"
    label = "drf_commons_serializers"
    verbose_name = "DRF Commons - Serializers"

from django.apps import AppConfig


class FiltersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_commons.filters"
    label = "drf_commons_filters"
    verbose_name = "DRF Commons - Advanced Filters"

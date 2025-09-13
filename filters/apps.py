from django.apps import AppConfig


class FiltersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_common.filters"
    label = "drf_common_filters"
    verbose_name = "DRF Common - Advanced Filters"
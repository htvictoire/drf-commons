from django.apps import AppConfig


class PaginationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_commons.pagination"
    label = "drf_commons_pagination"
    verbose_name = "DRF Commons - Pagination"

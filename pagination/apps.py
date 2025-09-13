from django.apps import AppConfig


class PaginationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_common.pagination"
    label = "drf_common_pagination"
    verbose_name = "DRF Common - Pagination"
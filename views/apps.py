from django.apps import AppConfig


class ViewsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_common.views"
    label = "drf_common_views"
    verbose_name = "DRF Common - Views"
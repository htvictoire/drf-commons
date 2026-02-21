from django.apps import AppConfig


class DrfCommonsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_commons"
    verbose_name = "DRF Commons"

    def ready(self):
        from drf_commons.utils.middleware_checker import (
            enforce_current_user_middleware_if_used,
        )

        enforce_current_user_middleware_if_used(
            "drf_commons.middlewares.current_user.CurrentUserMiddleware"
        )

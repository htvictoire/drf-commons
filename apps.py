from django.apps import AppConfig


class DrfCommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_commons"
    verbose_name = "DRF Commons - Complete Package"

    def ready(self):
        """Register all sub-apps when using the complete package."""
        from django.apps import apps

        # Sub-apps to auto-register
        sub_apps = [
            "drf_commons.current_user",
            "drf_commons.debug",
            "drf_commons.filters",
            "drf_commons.pagination",
            "drf_commons.response",
            "drf_commons.serializers",
            "drf_commons.views",
        ]

        # Only register sub-apps that aren't already in INSTALLED_APPS
        from django.conf import settings

        installed_apps = getattr(settings, "INSTALLED_APPS", [])

        for app_name in sub_apps:
            if app_name not in installed_apps:
                try:
                    apps.populate([app_name])
                except Exception:
                    # App might already be registered or have issues
                    pass

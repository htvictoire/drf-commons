from django.apps import AppConfig


class DrfCommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "drf_common"
    verbose_name = "DRF Common - Complete Package"

    def ready(self):
        """Register all sub-apps when using the complete package."""
        from django.apps import apps

        # Sub-apps to auto-register
        sub_apps = [
            "drf_common.current_user",
            "drf_common.debug",
            "drf_common.filters",
            "drf_common.pagination",
            "drf_common.response",
            "drf_common.serializers",
            "drf_common.views",
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

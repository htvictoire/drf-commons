"""
DRF Commons Library Settings

Centralized configuration management with COMMON_ namespace override support.
Settings are resolved dynamically on each access.
"""

from django.conf import settings as django_settings


DEFAULT_SETTINGS = {
    # Authentication & user management
    "LOCAL_USER_ATTR_NAME": "_current_user",
    # Debug & development
    "ENABLE_PROFILER": False,
    "DEBUG_SLOW_REQUEST_THRESHOLD": 1.0,
    "DEBUG_HIGH_QUERY_COUNT_THRESHOLD": 10,
    "DEBUG_SLOW_QUERY_THRESHOLD": 0.1,
    "DEBUG_LOG_FILE_MAX_BYTES": 10 * 1024 * 1024,
    "DEBUG_LOG_BACKUP_COUNT": 5,
    "DEBUG_LOG_DEBUG_FILE_MAX_BYTES": 20 * 1024 * 1024,
    "DEBUG_LOG_ERROR_FILE_MAX_BYTES": 5 * 1024 * 1024,
    "DEBUG_PROFILER_TOP_FUNCTIONS": 20,
    "DEBUG_PRETTY_PRINT_INDENT": 2,
    "DEBUG_PRETTY_PRINT_WIDTH": 120,
    "DEBUG_QUERYSET_SAMPLE_SIZE": 5,
    "DEBUG_LOG_SPECIFIC_FILE_MAX_BYTES": 5 * 1024 * 1024,
    "DEBUG_LOG_SPECIFIC_BACKUP_COUNT": 3,
    "DEBUG_TITLE_BORDER_PADDING": 8,
    "DEBUG_SQL_BORDER_LENGTH": 40,
    "DEBUG_SENSITIVE_HEADERS": ["authorization", "cookie", "x-api-key"],
    "DEBUG_ERROR_HTTP_STATUS": 500,
    "DEBUG_PROFILER_SORT_METHOD": "cumulative",
    "DEBUG_LOGS_BASE_DIR": "logs",
    "DEBUG_ENABLED_LOG_CATEGORIES": [
        "console",
        "main",
        "errors",
        "database_slow",
        "users",
        "api",
        "database",
        "models",
        "cache",
        "performance",
        "requests",
    ],
    "DEBUG_PRODUCTION_SAFE_CATEGORIES": ["errors", "performance", "database", "models"],
    # Data processing
    "IMPORT_BATCH_SIZE": 250,
    "BULK_OPERATION_BATCH_SIZE": 1000,
    "IMPORT_FAILED_ROWS_DISPLAY_LIMIT": 10,
    # Document export
    "EXPORTED_DOCS_DATE_FORMAT": "%Y-%m-%d %H:%M",
    "EXPORTED_DOCS_DEFAULT_MARGIN": 20,
    "EXPORTED_DOCS_PDF_TABLE_MARGIN": 20,
    "EXPORTED_DOCS_DEFAULT_FONT_SIZE": 12,
    "EXPORTED_DOCS_HEADER_FONT_SIZE": 12,
    "EXPORTED_DOCS_TITLE_FONT_SIZE": 14,
    "EXPORTED_DOCS_PDF_TABLE_ROW_HEIGHT": 20,
    "EXPORTED_DOCS_PDF_CELL_PADDING": 4,
    "EXPORTED_DOCS_PDF_HEADER_PADDING_V": 6,
    "EXPORTED_DOCS_PDF_HEADER_PADDING_H": 6,
    "EXPORTED_DOCS_PDF_HEADER_TO_TITLE_SPACING": 10,
    "EXPORTED_DOCS_PDF_TITLE_TO_TABLE_SPACING": 10,
    "EXPORTED_DOCS_DEFAULT_TABLE_HEADER_COLOR": "366092",
    "EXPORTED_DOCS_DEFAULT_TEXT_COLOR": "000000",
    "EXPORTED_DOCS_DEFAULT_BORDER_COLOR": "000000",
    "EXPORTED_DOCS_DEFAULT_ALTERNATE_ROW_COLOR": "F8F9FA",
    "EXPORTED_DOCS_PDF_AUTO_ORIENTATION": True,
    "EXPORTED_DOCS_PDF_AVG_CHAR_WIDTH": 6,
    "EXPORTED_DOCS_PDF_ROW_THRESHOLD_PERCENTAGE": 15,
    "EXPORTED_DOCS_AUTO_COLUMN_WIDTH": True,
    "EXPORTED_DOCS_MAX_COLUMN_WIDTH": 50,
}


class CommonSettings:
    """Manages library settings with namespace override support."""

    def get(self, key, default=None):
        """Retrieve setting value with COMMON_ override."""
        namespaced_key = f"COMMON_{key}"
        if hasattr(django_settings, namespaced_key):
            return getattr(django_settings, namespaced_key)
        if hasattr(django_settings, key):
            return getattr(django_settings, key)
        return default

    def __getattr__(self, name):
        if name in DEFAULT_SETTINGS:
            return self.get(name, DEFAULT_SETTINGS[name])
        raise AttributeError(f"Unknown setting '{name}'")


_settings = CommonSettings()


def __getattr__(name):
    if name in DEFAULT_SETTINGS:
        return _settings.get(name, DEFAULT_SETTINGS[name])
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def get_setting(key, default=None):
    """Get setting value with namespace override support."""
    fallback = DEFAULT_SETTINGS[key] if key in DEFAULT_SETTINGS and default is None else default
    return _settings.get(key, fallback)

"""
DRF Commons Library Settings

Centralized configuration management with COMMON_ namespace override support.
Settings defined here can be overridden in Django settings with COMMON_ prefix.
"""

from django.conf import settings as django_settings


class CommonSettings:
    """Manages library settings with namespace override support."""

    def get(self, key, default=None):
        """
        Retrieve setting value with namespace override.

        Checks COMMON_{key} first, then {key}, then returns default.
        """
        namespaced_key = f"COMMON_{key}"
        if hasattr(django_settings, namespaced_key):
            return getattr(django_settings, namespaced_key)

        if hasattr(django_settings, key):
            return getattr(django_settings, key)

        return default

    def __getattr__(self, name):
        """Enable direct attribute access."""
        return self.get(name)


_settings = CommonSettings()


# === AUTHENTICATION & USER MANAGEMENT ===
LOCAL_USER_ATTR_NAME = _settings.get("LOCAL_USER_ATTR_NAME", "_current_user")


# === DEBUG & DEVELOPMENT ===
ENABLE_PROFILER = _settings.get("ENABLE_PROFILER", False)

# Request performance thresholds
DEBUG_SLOW_REQUEST_THRESHOLD = _settings.get("DEBUG_SLOW_REQUEST_THRESHOLD", 1.0)
DEBUG_HIGH_QUERY_COUNT_THRESHOLD = _settings.get("DEBUG_HIGH_QUERY_COUNT_THRESHOLD", 10)
DEBUG_SLOW_QUERY_THRESHOLD = _settings.get("DEBUG_SLOW_QUERY_THRESHOLD", 0.1)

# Logging configuration
DEBUG_LOG_FILE_MAX_BYTES = _settings.get(
    "DEBUG_LOG_FILE_MAX_BYTES", 10 * 1024 * 1024
)  # 10MB
DEBUG_LOG_BACKUP_COUNT = _settings.get("DEBUG_LOG_BACKUP_COUNT", 5)
DEBUG_LOG_DEBUG_FILE_MAX_BYTES = _settings.get(
    "DEBUG_LOG_DEBUG_FILE_MAX_BYTES", 20 * 1024 * 1024
)  # 20MB
DEBUG_LOG_ERROR_FILE_MAX_BYTES = _settings.get(
    "DEBUG_LOG_ERROR_FILE_MAX_BYTES", 5 * 1024 * 1024
)  # 5MB

# Profiler settings
DEBUG_PROFILER_TOP_FUNCTIONS = _settings.get("DEBUG_PROFILER_TOP_FUNCTIONS", 20)

# Pretty print settings
DEBUG_PRETTY_PRINT_INDENT = _settings.get("DEBUG_PRETTY_PRINT_INDENT", 2)
DEBUG_PRETTY_PRINT_WIDTH = _settings.get("DEBUG_PRETTY_PRINT_WIDTH", 120)

# Query analysis settings
DEBUG_QUERYSET_SAMPLE_SIZE = _settings.get("DEBUG_QUERYSET_SAMPLE_SIZE", 5)

# Logging file sizes for specific handlers (in bytes)
DEBUG_LOG_SPECIFIC_FILE_MAX_BYTES = _settings.get(
    "DEBUG_LOG_SPECIFIC_FILE_MAX_BYTES", 5 * 1024 * 1024
)  # 5MB
DEBUG_LOG_SPECIFIC_BACKUP_COUNT = _settings.get("DEBUG_LOG_SPECIFIC_BACKUP_COUNT", 3)

# Debug display settings
DEBUG_TITLE_BORDER_PADDING = _settings.get("DEBUG_TITLE_BORDER_PADDING", 8)
DEBUG_SQL_BORDER_LENGTH = _settings.get("DEBUG_SQL_BORDER_LENGTH", 40)

# Security settings
DEBUG_SENSITIVE_HEADERS = _settings.get(
    "DEBUG_SENSITIVE_HEADERS", ["authorization", "cookie", "x-api-key"]
)
DEBUG_ERROR_HTTP_STATUS = _settings.get("DEBUG_ERROR_HTTP_STATUS", 500)

# Profiler settings
DEBUG_PROFILER_SORT_METHOD = _settings.get("DEBUG_PROFILER_SORT_METHOD", "cumulative")

# Logging directory settings
DEBUG_LOGS_BASE_DIR = _settings.get("DEBUG_LOGS_BASE_DIR", "logs")

# User-configurable log categories - includes both system handlers and debug categories
# Only enabled categories will have log directories created
DEBUG_ENABLED_LOG_CATEGORIES = _settings.get(
    "DEBUG_ENABLED_LOG_CATEGORIES",
    [
        # System handlers (can be disabled by users)
        "console",
        "main",
        "errors",
        "database_slow",
        # Debug categories
        "users",
        "api",
        "database",
        "models",
        "cache",
        "performance",
        "requests",
    ],
)

# Categories allowed in production environments when Django DEBUG=False
DEBUG_PRODUCTION_SAFE_CATEGORIES = _settings.get(
    "DEBUG_PRODUCTION_SAFE_CATEGORIES", ["errors", "performance", "database", "models"]
)


# === DATA PROCESSING ===
IMPORT_BATCH_SIZE = _settings.get("IMPORT_BATCH_SIZE", 250)


# === BULK OPERATIONS ===
BULK_OPERATION_BATCH_SIZE = _settings.get("BULK_OPERATION_BATCH_SIZE", 1000)

# Import operation settings
IMPORT_FAILED_ROWS_DISPLAY_LIMIT = _settings.get("IMPORT_FAILED_ROWS_DISPLAY_LIMIT", 10)


# === DOCUMENT EXPORT ===

# Date format for exported documents
EXPORTED_DOCS_DATE_FORMAT = _settings.get("EXPORTED_DOCS_DATE_FORMAT", "%Y-%m-%d %H:%M")

# Layout settings
EXPORTED_DOCS_DEFAULT_MARGIN = _settings.get("EXPORTED_DOCS_DEFAULT_MARGIN", 20)
EXPORTED_DOCS_PDF_TABLE_MARGIN = _settings.get("EXPORTED_DOCS_PDF_TABLE_MARGIN", 20)

# Typography settings
EXPORTED_DOCS_DEFAULT_FONT_SIZE = _settings.get("EXPORTED_DOCS_DEFAULT_FONT_SIZE", 12)
EXPORTED_DOCS_HEADER_FONT_SIZE = _settings.get("EXPORTED_DOCS_HEADER_FONT_SIZE", 12)
EXPORTED_DOCS_TITLE_FONT_SIZE = _settings.get("EXPORTED_DOCS_TITLE_FONT_SIZE", 14)

# Table layout settings
EXPORTED_DOCS_PDF_TABLE_ROW_HEIGHT = _settings.get(
    "EXPORTED_DOCS_PDF_TABLE_ROW_HEIGHT", 20
)
EXPORTED_DOCS_PDF_CELL_PADDING = _settings.get("EXPORTED_DOCS_PDF_CELL_PADDING", 4)
EXPORTED_DOCS_PDF_HEADER_PADDING_V = _settings.get(
    "EXPORTED_DOCS_PDF_HEADER_PADDING_V", 6
)
EXPORTED_DOCS_PDF_HEADER_PADDING_H = _settings.get(
    "EXPORTED_DOCS_PDF_HEADER_PADDING_H", 6
)

# Spacing settings
EXPORTED_DOCS_PDF_HEADER_TO_TITLE_SPACING = _settings.get(
    "EXPORTED_DOCS_PDF_HEADER_TO_TITLE_SPACING", 10
)
EXPORTED_DOCS_PDF_TITLE_TO_TABLE_SPACING = _settings.get(
    "EXPORTED_DOCS_PDF_TITLE_TO_TABLE_SPACING", 10
)

# Color settings
EXPORTED_DOCS_DEFAULT_TABLE_HEADER_COLOR = _settings.get(
    "EXPORTED_DOCS_DEFAULT_TABLE_HEADER_COLOR", "366092"
)
EXPORTED_DOCS_DEFAULT_TEXT_COLOR = _settings.get(
    "EXPORTED_DOCS_DEFAULT_TEXT_COLOR", "000000"
)
EXPORTED_DOCS_DEFAULT_BORDER_COLOR = _settings.get(
    "EXPORTED_DOCS_DEFAULT_BORDER_COLOR", "000000"
)
EXPORTED_DOCS_DEFAULT_ALTERNATE_ROW_COLOR = _settings.get(
    "EXPORTED_DOCS_DEFAULT_ALTERNATE_ROW_COLOR", "F8F9FA"
)

# PDF-specific options
EXPORTED_DOCS_PDF_AUTO_ORIENTATION = _settings.get(
    "EXPORTED_DOCS_PDF_AUTO_ORIENTATION", True
)
EXPORTED_DOCS_PDF_AVG_CHAR_WIDTH = _settings.get("EXPORTED_DOCS_PDF_AVG_CHAR_WIDTH", 6)
EXPORTED_DOCS_PDF_ROW_THRESHOLD_PERCENTAGE = _settings.get(
    "EXPORTED_DOCS_PDF_ROW_THRESHOLD_PERCENTAGE", 15
)

# Excel-specific options
EXPORTED_DOCS_AUTO_COLUMN_WIDTH = _settings.get("EXPORTED_DOCS_AUTO_COLUMN_WIDTH", True)
EXPORTED_DOCS_MAX_COLUMN_WIDTH = _settings.get("EXPORTED_DOCS_MAX_COLUMN_WIDTH", 50)


def get_setting(key, default=None):
    """Get setting value with namespace override support."""
    return _settings.get(key, default)


def clear_settings_cache():
    """Backward-compatible no-op; settings are resolved without local caching."""
    return None

"""
DRF Common Library Settings

Centralized configuration management with COMMON_ namespace override support.
Settings defined here can be overridden in Django settings with COMMON_ prefix.
"""

from django.conf import settings as django_settings


class CommonSettings:
    """Manages library settings with namespace override support."""
    
    def __init__(self):
        self._cached_settings = {}
    
    def get(self, key, default=None):
        """
        Retrieve setting value with namespace override.
        
        Checks COMMON_{key} first, then {key}, then returns default.
        """
        if key in self._cached_settings:
            return self._cached_settings[key]
        
        namespaced_key = f'COMMON_{key}'
        if hasattr(django_settings, namespaced_key):
            value = getattr(django_settings, namespaced_key)
            self._cached_settings[key] = value
            return value
        
        if hasattr(django_settings, key):
            value = getattr(django_settings, key)
            self._cached_settings[key] = value
            return value
        
        self._cached_settings[key] = default
        return default
    
    def __getattr__(self, name):
        """Enable direct attribute access."""
        return self.get(name)


_settings = CommonSettings()

# Debug and development
DEBUG_ENABLED = _settings.get('DEBUG_ENABLED', getattr(django_settings, 'DEBUG', False))
ENABLE_PROFILER = _settings.get('ENABLE_PROFILER', False)

# Authentication
LOCAL_USER_ATTR_NAME = _settings.get('LOCAL_USER_ATTR_NAME', '_current_user')

# Data processing
IMPORT_BATCH_SIZE = _settings.get('IMPORT_BATCH_SIZE', 250)

# Document export - Layout
EXPORTED_DOCS_DEFAULT_MARGIN = _settings.get('EXPORTED_DOCS_DEFAULT_MARGIN', 20)
EXPORTED_DOCS_PDF_TABLE_MARGIN = _settings.get('EXPORTED_DOCS_PDF_TABLE_MARGIN', 20)

# Document export - Typography
EXPORTED_DOCS_DEFAULT_FONT_SIZE = _settings.get('EXPORTED_DOCS_DEFAULT_FONT_SIZE', 12)
EXPORTED_DOCS_HEADER_FONT_SIZE = _settings.get('EXPORTED_DOCS_HEADER_FONT_SIZE', 12)
EXPORTED_DOCS_TITLE_FONT_SIZE = _settings.get('EXPORTED_DOCS_TITLE_FONT_SIZE', 14)

# Document export - Table layout
EXPORTED_DOCS_PDF_TABLE_ROW_HEIGHT = _settings.get('EXPORTED_DOCS_PDF_TABLE_ROW_HEIGHT', 20)
EXPORTED_DOCS_PDF_CELL_PADDING = _settings.get('EXPORTED_DOCS_PDF_CELL_PADDING', 4)
EXPORTED_DOCS_PDF_HEADER_PADDING_V = _settings.get('EXPORTED_DOCS_PDF_HEADER_PADDING_V', 6)
EXPORTED_DOCS_PDF_HEADER_PADDING_H = _settings.get('EXPORTED_DOCS_PDF_HEADER_PADDING_H', 6)

# Document export - Spacing
EXPORTED_DOCS_PDF_HEADER_TO_TITLE_SPACING = _settings.get('EXPORTED_DOCS_PDF_HEADER_TO_TITLE_SPACING', 10)
EXPORTED_DOCS_PDF_TITLE_TO_TABLE_SPACING = _settings.get('EXPORTED_DOCS_PDF_TITLE_TO_TABLE_SPACING', 10)

# Document export - Colors
EXPORTED_DOCS_DEFAULT_TABLE_HEADER_COLOR = _settings.get('EXPORTED_DOCS_DEFAULT_TABLE_HEADER_COLOR', '366092')
EXPORTED_DOCS_DEFAULT_TEXT_COLOR = _settings.get('EXPORTED_DOCS_DEFAULT_TEXT_COLOR', '000000')
EXPORTED_DOCS_DEFAULT_BORDER_COLOR = _settings.get('EXPORTED_DOCS_DEFAULT_BORDER_COLOR', '000000')
EXPORTED_DOCS_DEFAULT_ALTERNATE_ROW_COLOR = _settings.get('EXPORTED_DOCS_DEFAULT_ALTERNATE_ROW_COLOR', 'F8F9FA')

# Document export - PDF options
EXPORTED_DOCS_PDF_AUTO_ORIENTATION = _settings.get('EXPORTED_DOCS_PDF_AUTO_ORIENTATION', True)
EXPORTED_DOCS_PDF_AVG_CHAR_WIDTH = _settings.get('EXPORTED_DOCS_PDF_AVG_CHAR_WIDTH', 6)
EXPORTED_DOCS_PDF_ROW_THRESHOLD_PERCENTAGE = _settings.get('EXPORTED_DOCS_PDF_ROW_THRESHOLD_PERCENTAGE', 15)

# Document export - Excel options
EXPORTED_DOCS_AUTO_COLUMN_WIDTH = _settings.get('EXPORTED_DOCS_AUTO_COLUMN_WIDTH', True)
EXPORTED_DOCS_MAX_COLUMN_WIDTH = _settings.get('EXPORTED_DOCS_MAX_COLUMN_WIDTH', 50)


def get_setting(key, default=None):
    """Get setting value with namespace override support."""
    return _settings.get(key, default)


def clear_settings_cache():
    """Clear cached settings values."""
    _settings._cached_settings.clear()
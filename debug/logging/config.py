"""
Main logging configuration orchestration.
"""

from pathlib import Path
from common_conf import settings
from ..core.categories import Categories
from .formatters import get_formatters
from .directories import create_log_directories
from .handlers import build_handlers, filter_available_handlers
from .loggers import build_loggers


def build_logging_config(base_dir, debug_mode=False):
    """
    Build logging configuration for enabled categories.

    Args:
        base_dir (Path): Base directory for log files
        debug_mode (bool): Whether to enable debug-level logging

    Returns:
        dict: Python logging configuration dictionary
    """
    enabled_categories = Categories.get_enabled()
    logs_dir = Path(base_dir) / str(settings.DEBUG_LOGS_BASE_DIR)

    create_log_directories(logs_dir, enabled_categories)

    handlers = build_handlers(logs_dir, enabled_categories, debug_mode)
    loggers = build_loggers(enabled_categories, debug_mode)

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': get_formatters(),
        'handlers': handlers,
        'loggers': loggers,
        'root': {
            'handlers': filter_available_handlers(['console', 'main', 'errors'], handlers),
            'level': 'INFO'
        }
    }
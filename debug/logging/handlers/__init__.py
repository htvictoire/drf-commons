"""
Handler building functions.
"""

import logging
from ...core.categories import Categories
from .specs import HANDLER_SPECS

logger = logging.getLogger(__name__)


def build_handlers(logs_dir, enabled_categories, debug_mode):
    """
    Build handler configuration for enabled categories.

    Args:
        logs_dir (Path): Base log directory
        enabled_categories (set): Set of enabled category names
        debug_mode (bool): Whether debug mode is active

    Returns:
        dict: Handler configuration mapping
    """
    handlers = {}

    for handler_key, spec in HANDLER_SPECS.items():
        # Skip category-specific handlers if category not enabled
        if _should_skip_handler(handler_key, spec, enabled_categories):
            continue

        try:
            if spec.get('class') == 'logging.StreamHandler':
                handlers[handler_key] = _build_console_handler(spec, debug_mode)
            else:
                handlers[handler_key] = _build_file_handler(logs_dir, spec)
        except (TypeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to create handler '{handler_key}': {e}")
            continue

    return handlers


def filter_available_handlers(handler_names, available_handlers):
    """Filter handler names to only include those that exist."""
    return [name for name in handler_names if name in available_handlers]


def _should_skip_handler(handler_key, spec, enabled_categories):
    """Check if handler should be skipped based on category enablement."""
    # Skip if handler is for disabled category
    if handler_key in Categories.ALL and handler_key not in enabled_categories:
        return True

    # Skip if handler requires a category that's disabled
    required_category = spec.get('requires_category')
    if required_category and required_category not in enabled_categories:
        return True

    return False


def _build_console_handler(spec, debug_mode):
    """Build console handler configuration."""
    return {
        'class': 'logging.StreamHandler',
        'level': 'DEBUG' if debug_mode else spec['level'],
        'formatter': 'verbose'
    }


def _build_file_handler(logs_dir, spec):
    """Build rotating file handler configuration."""
    try:
        file_path = logs_dir / spec['file']
        return {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(file_path),
            'maxBytes': spec['max_bytes'],
            'backupCount': spec['backup_count'],
            'level': spec['level'],
            'formatter': 'verbose'
        }
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid file path in handler spec: {spec.get('file', 'unknown')} - {e}")
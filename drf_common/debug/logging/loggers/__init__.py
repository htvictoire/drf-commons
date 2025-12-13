"""
Logger building functions.
"""

import logging

from ...core.categories import Categories
from .specs import LOGGER_SPECS

logger = logging.getLogger(__name__)


def build_loggers(enabled_categories, debug_mode):
    """
    Build logger configuration for enabled categories.

    Args:
        enabled_categories (set): Set of enabled category names
        debug_mode (bool): Whether debug mode is active

    Returns:
        dict: Logger configuration mapping
    """
    loggers = {}

    for logger_name, spec in LOGGER_SPECS.items():
        # Skip if logger requires disabled category
        required_category = spec.get("requires_category")
        if required_category and required_category not in enabled_categories:
            continue

        handlers = resolve_logger_handlers(spec, enabled_categories, debug_mode)

        if handlers:  # Only create logger if it has handlers
            loggers[logger_name] = {
                "handlers": handlers,
                "level": get_logger_level(spec, debug_mode),
                "propagate": spec.get("propagate", False),
            }
        else:
            logger.debug(f"Logger '{logger_name}' has no available handlers - skipped")

    return loggers


def resolve_logger_handlers(spec, enabled_categories, debug_mode):
    """Resolve handler names for logger, filtering disabled categories."""
    handler_names = spec["handlers"]

    # Add console handler for specific loggers in debug mode
    if debug_mode and spec.get("console_in_debug"):
        handler_names = [*handler_names, "console"]

    # Filter out handlers for disabled categories
    available_handlers = [
        name
        for name in handler_names
        if name not in Categories.ALL or name in enabled_categories
    ]

    return available_handlers


def get_logger_level(spec, debug_mode):
    """Get appropriate log level for logger based on mode."""
    if debug_mode and "level_debug" in spec:
        return spec["level_debug"]
    elif not debug_mode and "level_production" in spec:
        return spec["level_production"]
    else:
        return spec.get("level", "INFO")

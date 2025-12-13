"""
Data-driven logging configuration builder.
"""

from .config import build_logging_config


def get_logging_config(base_dir, debug=False):
    """
    Get logging configuration for enabled debug categories.

    Args:
        base_dir (str|Path): Base directory for log files
        debug (bool): Enable debug-level logging and console output

    Returns:
        dict: Python logging configuration dictionary compatible with dictConfig()
    """
    return build_logging_config(base_dir, debug)

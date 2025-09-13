"""
Log directory management.
"""


def create_log_directories(logs_dir, enabled_categories):
    """Create necessary log directories for enabled categories."""
    logs_dir.mkdir(exist_ok=True)

    # Create category-specific directories
    for category in enabled_categories:
        (logs_dir / category).mkdir(exist_ok=True)

    # Create shared directories for system handlers
    (logs_dir / 'errors').mkdir(exist_ok=True)
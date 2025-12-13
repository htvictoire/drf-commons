"""
Handler specifications for logging configuration.
"""

from drf_common.common_conf import settings

from ...core.categories import Categories

# Handler specifications for each logging target
HANDLER_SPECS = {
    # System handlers - always available infrastructure
    "console": {"class": "logging.StreamHandler", "level": "INFO"},
    "main": {
        "file": "main.log",
        "level": "INFO",
        "max_bytes": settings.DEBUG_LOG_FILE_MAX_BYTES,
        "backup_count": settings.DEBUG_LOG_BACKUP_COUNT,
    },
    "errors": {
        "file": "errors/errors.log",
        "level": "ERROR",
        "max_bytes": settings.DEBUG_LOG_ERROR_FILE_MAX_BYTES,
        "backup_count": settings.DEBUG_LOG_BACKUP_COUNT,
    },
    "database_slow": {
        "file": "database/slow_queries.log",
        "level": "WARNING",
        "max_bytes": settings.DEBUG_LOG_SPECIFIC_FILE_MAX_BYTES,
        "backup_count": settings.DEBUG_LOG_SPECIFIC_BACKUP_COUNT,
        "requires_category": Categories.DATABASE,
    },
    # Category handlers - only exist when category enabled
    Categories.USERS: {
        "file": "users/users.log",
        "level": "INFO",
        "max_bytes": settings.DEBUG_LOG_SPECIFIC_FILE_MAX_BYTES,
        "backup_count": settings.DEBUG_LOG_SPECIFIC_BACKUP_COUNT,
    },
    Categories.API: {
        "file": "api/api.log",
        "level": "INFO",
        "max_bytes": settings.DEBUG_LOG_FILE_MAX_BYTES,
        "backup_count": settings.DEBUG_LOG_BACKUP_COUNT,
    },
    Categories.DATABASE: {
        "file": "database/queries.log",
        "level": "INFO",
        "max_bytes": settings.DEBUG_LOG_FILE_MAX_BYTES,
        "backup_count": settings.DEBUG_LOG_BACKUP_COUNT,
    },
    Categories.PERFORMANCE: {
        "file": "performance/performance.log",
        "level": "INFO",
        "max_bytes": settings.DEBUG_LOG_SPECIFIC_FILE_MAX_BYTES,
        "backup_count": settings.DEBUG_LOG_SPECIFIC_BACKUP_COUNT,
    },
    Categories.CACHE: {
        "file": "cache/operations.log",
        "level": "INFO",
        "max_bytes": settings.DEBUG_LOG_SPECIFIC_FILE_MAX_BYTES,
        "backup_count": settings.DEBUG_LOG_SPECIFIC_BACKUP_COUNT,
    },
    Categories.MODELS: {
        "file": "models/changes.log",
        "level": "INFO",
        "max_bytes": settings.DEBUG_LOG_SPECIFIC_FILE_MAX_BYTES,
        "backup_count": settings.DEBUG_LOG_SPECIFIC_BACKUP_COUNT,
    },
    Categories.REQUESTS: {
        "file": "requests/requests.log",
        "level": "INFO",
        "max_bytes": settings.DEBUG_LOG_FILE_MAX_BYTES,
        "backup_count": settings.DEBUG_LOG_BACKUP_COUNT,
    },
}

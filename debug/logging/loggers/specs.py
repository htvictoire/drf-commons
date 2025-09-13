"""
Logger specifications for logging configuration.
"""

from ...core.categories import Categories


# Logger to handler mappings
LOGGER_SPECS = {
    'django': {
        'handlers': ['console', 'main', 'errors'],
        'level': 'INFO',
        'propagate': False
    },
    'django.db.backends': {
        'handlers': [Categories.DATABASE],
        'level_debug': 'DEBUG',
        'level_production': 'INFO',
        'propagate': False,
        'console_in_debug': True
    },
    'django.security': {
        'handlers': ['errors', 'console'],
        'level': 'WARNING',
        'propagate': False
    },
    f'{Categories.USERS}.auth': {
        'handlers': [Categories.USERS],
        'level': 'INFO',
        'propagate': False,
        'requires_category': Categories.USERS
    },
    f'{Categories.USERS}.crud': {
        'handlers': [Categories.USERS],
        'level': 'INFO',
        'propagate': False,
        'requires_category': Categories.USERS
    },
    f'{Categories.API}.views': {
        'handlers': [Categories.API],
        'level': 'INFO',
        'propagate': False,
        'requires_category': Categories.API
    },
    f'{Categories.API}.performance': {
        'handlers': [Categories.API],
        'level': 'INFO',
        'propagate': False,
        'requires_category': Categories.API
    },
    f'{Categories.DATABASE}.queries': {
        'handlers': [Categories.DATABASE],
        'level': 'INFO',
        'propagate': False,
        'requires_category': Categories.DATABASE
    },
    f'{Categories.DATABASE}.slow': {
        'handlers': ['database_slow'],
        'level': 'WARNING',
        'propagate': False,
        'requires_category': Categories.DATABASE
    },
    f'{Categories.MODELS}.changes': {
        'handlers': [Categories.MODELS],
        'level': 'INFO',
        'propagate': False,
        'requires_category': Categories.MODELS
    },
    f'{Categories.CACHE}.operations': {
        'handlers': [Categories.CACHE],
        'level': 'INFO',
        'propagate': False,
        'requires_category': Categories.CACHE
    },
    f'{Categories.PERFORMANCE}': {
        'handlers': [Categories.PERFORMANCE],
        'level': 'INFO',
        'propagate': False,
        'requires_category': Categories.PERFORMANCE
    },
    'middleware.debug': {
        'handlers': [Categories.REQUESTS],
        'level': 'INFO',
        'propagate': False,
        'requires_category': Categories.REQUESTS
    },
    'middleware.sql': {
        'handlers': [Categories.DATABASE],
        'level': 'INFO',
        'propagate': False,
        'requires_category': Categories.DATABASE
    },
    'middleware.profiler': {
        'handlers': [Categories.PERFORMANCE],
        'level': 'INFO',
        'propagate': False,
        'requires_category': Categories.PERFORMANCE
    },
    f'{Categories.ERRORS}': {
        'handlers': ['errors', 'console'],
        'level': 'ERROR',
        'propagate': False
    }
}
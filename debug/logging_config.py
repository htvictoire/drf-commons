"""
Logging configuration for structured logging across the application.
"""

import os
from pathlib import Path


def get_logging_config(base_dir, debug=False):
    """
    Get logging configuration for different environments.
    
    Args:
        base_dir (Path): Base directory of the project
        debug (bool): Whether debug mode is enabled
    
    Returns:
        dict: Logging configuration
    """
    logs_dir = base_dir / 'logs'
    
    # Ensure logs directory exists
    logs_dir.mkdir(exist_ok=True)
    for subdir in ['users', 'api', 'database', 'models', 'cache', 'performance', 'errors', 'requests']:
        (logs_dir / subdir).mkdir(exist_ok=True)
    
    # Base logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {funcName}:{lineno} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {asctime} {message}',
                'style': '{',
            },
            'json': {
                'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG' if debug else 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
            'main_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'base_api.log',
                'maxBytes': 1024*1024*10,  # 10MB
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'error_file': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'errors' / 'errors.log',
                'maxBytes': 1024*1024*5,  # 5MB
                'backupCount': 3,
                'formatter': 'verbose',
            },
            # User-related logs
            'users_auth_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'users' / 'auth.log',
                'maxBytes': 1024*1024*5,
                'backupCount': 3,
                'formatter': 'verbose',
            },
            'users_crud_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'users' / 'crud.log',
                'maxBytes': 1024*1024*5,
                'backupCount': 3,
                'formatter': 'verbose',
            },
            # API logs
            'api_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'api' / 'api.log',
                'maxBytes': 1024*1024*10,
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'api_performance_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'api' / 'performance.log',
                'maxBytes': 1024*1024*5,
                'backupCount': 3,
                'formatter': 'verbose',
            },
            # Database logs
            'database_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'database' / 'queries.log',
                'maxBytes': 1024*1024*10,
                'backupCount': 5,
                'formatter': 'verbose',
            },
            'database_slow_file': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'database' / 'slow_queries.log',
                'maxBytes': 1024*1024*5,
                'backupCount': 3,
                'formatter': 'verbose',
            },
            # Model changes
            'models_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'models' / 'changes.log',
                'maxBytes': 1024*1024*5,
                'backupCount': 3,
                'formatter': 'verbose',
            },
            # Cache operations
            'cache_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'cache' / 'operations.log',
                'maxBytes': 1024*1024*5,
                'backupCount': 3,
                'formatter': 'verbose',
            },
            # Performance logs
            'performance_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'performance' / 'performance.log',
                'maxBytes': 1024*1024*5,
                'backupCount': 3,
                'formatter': 'verbose',
            },
            # Request logs
            'requests_file': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': logs_dir / 'requests' / 'requests.log',
                'maxBytes': 1024*1024*10,
                'backupCount': 5,
                'formatter': 'verbose',
            },
        },
        'loggers': {
            # Django core loggers
            'django': {
                'handlers': ['console', 'main_file', 'error_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['database_file'] + (['console'] if debug else []),
                'level': 'DEBUG' if debug else 'INFO',
                'propagate': False,
            },
            'django.security': {
                'handlers': ['error_file', 'console'],
                'level': 'WARNING',
                'propagate': False,
            },
            # Application loggers - file only
            'base_api': {
                'handlers': ['main_file', 'error_file'],
                'level': 'DEBUG' if debug else 'INFO',
                'propagate': False,
            },
            'common': {
                'handlers': ['main_file', 'error_file'],
                'level': 'DEBUG' if debug else 'INFO',
                'propagate': False,
            },
            # Feature-specific loggers - file only
            'users.auth': {
                'handlers': ['users_auth_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'users.crud': {
                'handlers': ['users_crud_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'api.views': {
                'handlers': ['api_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'api.performance': {
                'handlers': ['api_performance_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'database.queries': {
                'handlers': ['database_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'database.slow': {
                'handlers': ['database_slow_file'],
                'level': 'WARNING',
                'propagate': False,
            },
            'models.changes': {
                'handlers': ['models_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'cache.operations': {
                'handlers': ['cache_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'performance': {
                'handlers': ['performance_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'middleware.debug': {
                'handlers': ['requests_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'middleware.sql': {
                'handlers': ['database_file'],
                'level': 'INFO',
                'propagate': False,
            },
            'middleware.profiler': {
                'handlers': ['performance_file'],
                'level': 'INFO',
                'propagate': False,
            },
            # Error and exception loggers
            'errors': {
                'handlers': ['error_file', 'console'],
                'level': 'ERROR',
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console', 'main_file', 'error_file'],
            'level': 'INFO',
        },
    }
    
    # Add debug-specific handlers and loggers
    if debug:
        config['handlers']['debug_file'] = {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': logs_dir / 'debug.log',
            'maxBytes': 1024*1024*20,  # 20MB for debug logs
            'backupCount': 3,
            'formatter': 'verbose',
        }
        
        # Add debug handler to main loggers
        for logger_name in ['base_api', 'common']:
            config['loggers'][logger_name]['handlers'].append('debug_file')
    
    return config


def setup_custom_loggers():
    """
    Set up custom loggers for specific use cases.
    """
    import logging
    
    # Create specialized loggers
    loggers = {
        'audit': logging.getLogger('audit'),
        'security': logging.getLogger('security'),
        'business': logging.getLogger('business'),
        'integration': logging.getLogger('integration'),
    }
    
    return loggers
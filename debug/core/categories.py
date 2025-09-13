"""
Debug category definitions and management.
"""

import logging
from django.conf import settings as django_settings
from common_conf import settings


class NullLogger:
    """Logger that absorbs all calls when category is disabled."""
    __slots__ = ()  # No instance variables needed - memory efficient
    
    def debug(self, msg, *args, **kwargs):
        pass
    
    def info(self, msg, *args, **kwargs):
        pass
    
    def warning(self, msg, *args, **kwargs):
        pass
    
    def error(self, msg, *args, **kwargs):
        pass
    
    def critical(self, msg, *args, **kwargs):
        pass
    
    def log(self, level, msg, *args, **kwargs):
        pass
    
    def exception(self, msg, *args, **kwargs):
        pass
    
    def addHandler(self, hdlr):
        pass
    
    def removeHandler(self, hdlr):
        pass
    
    def setLevel(self, level):
        pass
    


class Categories:
    """Debug category constants and management."""
    
    # Debug categories - feature-specific logging
    USERS = 'users'
    API = 'api'
    DATABASE = 'database'
    MODELS = 'models'
    CACHE = 'cache'
    PERFORMANCE = 'performance'
    ERRORS = 'errors'
    REQUESTS = 'requests'
    
    ALL = [USERS, API, DATABASE, MODELS, CACHE, PERFORMANCE, ERRORS, REQUESTS]
    
    # Singleton null logger instance
    _null_logger = NullLogger()
    
    @classmethod
    def is_enabled(cls, category):
        """
        Check if debug category is enabled based on environment and configuration.
        
        In production (DEBUG=False), only categories listed in DEBUG_PRODUCTION_SAFE_CATEGORIES
        are allowed. In development (DEBUG=True), all categories in DEBUG_ENABLED_LOG_CATEGORIES
        are allowed.
        
        Args:
            category (str): Debug category to check
            
        Returns:
            bool: True if category should log, False otherwise
        """
        # Category must be explicitly enabled
        if category not in settings.DEBUG_ENABLED_LOG_CATEGORIES:
            return False
        
        # In production, restrict to safe categories only
        if not django_settings.DEBUG:
            return category in settings.DEBUG_PRODUCTION_SAFE_CATEGORIES
        
        # In development, all enabled categories are allowed
        return True
    
    @classmethod
    def get_enabled(cls):
        return set(settings.DEBUG_ENABLED_LOG_CATEGORIES)
    
    @classmethod
    def get_logger(cls, name, category=None):
        """
        Get logger for category with null object pattern.
        
        Args:
            name (str): Logger name
            category (str, optional): Debug category. If None, always creates logger.
            
        Returns:
            logging.Logger or NullLogger: Real logger if category enabled, 
            null logger if disabled (eliminates need for None checks)
        """
        if category and not cls.is_enabled(category):
            return cls._null_logger
        return logging.getLogger(name)
"""
Logging utilities for structured logging.
"""

import logging
import time
import functools
from django.conf import settings as django_settings
from django.db import connection
from .. import settings


def get_logger(name, log_file=None):
    """
    Get a logger with specific configuration for different features.
    
    Args:
        name (str): Logger name (e.g., 'users.auth', 'users.crud', 'api.views')
        log_file (str): Optional specific log file name
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if log_file and not logger.handlers:
        # Create file handler for specific log file
        file_handler = logging.FileHandler(
            django_settings.BASE_DIR / 'logs' / f"{log_file}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.setLevel(logging.DEBUG)
    
    return logger


def log_function_call(logger_name=None, log_args=True, log_result=True):
    """
    Decorator to log function calls with arguments and results.
    
    Args:
        logger_name (str): Name of the logger to use
        log_args (bool): Whether to log function arguments
        log_result (bool): Whether to log function result
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or f"{func.__module__}.{func.__name__}")
            
            # Log function entry
            if log_args:
                logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            else:
                logger.debug(f"Calling {func.__name__}")
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log function exit
                if log_result:
                    logger.debug(f"{func.__name__} completed in {execution_time:.4f}s, result={result}")
                else:
                    logger.debug(f"{func.__name__} completed in {execution_time:.4f}s")
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.4f}s with error: {e}")
                raise
        
        return wrapper
    return decorator


def log_db_query(query_type=""):
    """
    Log database queries for debugging performance issues.
    
    Args:
        query_type (str): Type of query for categorization
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger('database.queries', 'database')
            
            # Reset queries count
            initial_queries = len(connection.queries)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Calculate new queries
                new_queries = len(connection.queries) - initial_queries
                
                logger.info(
                    f"{query_type} {func.__name__}: {new_queries} queries in {execution_time:.4f}s"
                )
                
                # Log individual queries in debug mode
                if settings.DEBUG_ENABLED and new_queries > 0:
                    for query in connection.queries[initial_queries:]:
                        logger.debug(f"SQL: {query['sql']} (Time: {query['time']}s)")
                
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{query_type} {func.__name__} failed after {execution_time:.4f}s: {e}")
                raise
        
        return wrapper
    return decorator


class StructuredLogger:
    """
    Structured logger for consistent logging across the application.
    """
    
    def __init__(self, name, log_file=None):
        self.logger = get_logger(name, log_file)
    
    def log_user_action(self, user, action, resource=None, details=None):
        """Log user actions for audit trail."""
        user_id = getattr(user, 'id', 'anonymous')
        username = getattr(user, 'username', 'anonymous')
        
        message = f"User {username} (ID: {user_id}) performed {action}"
        if resource:
            message += f" on {resource}"
        if details:
            message += f" - Details: {details}"
        
        self.logger.info(message)
    
    def log_api_request(self, request, response=None, duration=None):
        """Log API requests and responses."""
        message = f"{request.method} {request.path}"
        if hasattr(request, 'user') and request.user.is_authenticated:
            message += f" by {request.user.username}"
        
        if response:
            message += f" - Status: {response.status_code}"
        
        if duration:
            message += f" - Duration: {duration:.4f}s"
        
        self.logger.info(message)
    
    def log_error(self, error, context=None):
        """Log errors with context."""
        message = f"Error: {str(error)}"
        if context:
            message += f" - Context: {context}"
        
        self.logger.error(message, exc_info=True)
    
    def log_performance(self, operation, duration, details=None):
        """Log performance metrics."""
        message = f"Performance: {operation} took {duration:.4f}s"
        if details:
            message += f" - {details}"
        
        self.logger.info(message)
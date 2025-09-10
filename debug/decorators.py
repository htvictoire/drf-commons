"""
Debug decorators for views, functions, and classes.
"""

import time
import functools
import traceback
from .. import settings
from django.http import JsonResponse
from .logger import get_logger


def debug_view(logger_name=None):
    """
    Decorator for Django views to add debugging information.
    
    Args:
        logger_name (str): Name of the logger to use
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not settings.DEBUG_ENABLED:
                return view_func(request, *args, **kwargs)
            
            logger = get_logger(logger_name or f"views.{view_func.__name__}", 'views')
            start_time = time.time()
            
            # Log request details
            logger.debug(f"View {view_func.__name__} called")
            logger.debug(f"Method: {request.method}")
            logger.debug(f"Path: {request.path}")
            logger.debug(f"User: {getattr(request.user, 'username', 'Anonymous')}")
            logger.debug(f"GET params: {dict(request.GET)}")
            
            if request.method == 'POST':
                logger.debug(f"POST data: {dict(request.POST)}")
            
            try:
                response = view_func(request, *args, **kwargs)
                duration = time.time() - start_time
                
                logger.debug(f"View {view_func.__name__} completed in {duration:.4f}s")
                logger.debug(f"Response status: {getattr(response, 'status_code', 'Unknown')}")
                
                return response
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"View {view_func.__name__} failed after {duration:.4f}s: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise
        
        return wrapper
    return decorator


def time_it(logger_name=None, threshold=None):
    """
    Decorator to measure and log execution time.
    
    Args:
        logger_name (str): Name of the logger to use
        threshold (float): Only log if execution time exceeds threshold (seconds)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or f"performance.{func.__name__}", 'performance')
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                if threshold is None or duration > threshold:
                    logger.info(f"{func.__name__} executed in {duration:.4f}s")
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.warning(f"{func.__name__} failed after {duration:.4f}s: {e}")
                raise
        
        return wrapper
    return decorator


def log_exceptions(logger_name=None, reraise=True):
    """
    Decorator to log exceptions with full traceback.
    
    Args:
        logger_name (str): Name of the logger to use
        reraise (bool): Whether to reraise the exception after logging
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or f"errors.{func.__name__}", 'errors')
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Exception in {func.__name__}: {e}",
                    exc_info=True,
                    extra={
                        'function': func.__name__,
                        'args': str(args),
                        'kwargs': str(kwargs),
                        'exception_type': type(e).__name__,
                    }
                )
                
                if reraise:
                    raise
                return None
        
        return wrapper
    return decorator


def debug_api_view(log_request_body=False):
    """
    Decorator for API views with detailed debugging.
    
    Args:
        log_request_body (bool): Whether to log request body (be careful with sensitive data)
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not settings.DEBUG_ENABLED:
                return view_func(request, *args, **kwargs)
            
            logger = get_logger(f"api.{view_func.__name__}", 'api')
            start_time = time.time()
            
            # Log API request details
            logger.info(f"API {request.method} {request.path}")
            logger.debug(f"Headers: {dict(request.headers)}")
            logger.debug(f"Query params: {dict(request.GET)}")
            
            if log_request_body and hasattr(request, 'body'):
                try:
                    logger.debug(f"Request body: {request.body.decode('utf-8')}")
                except:
                    logger.debug("Request body: <binary data>")
            
            try:
                response = view_func(request, *args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"API {request.method} {request.path} - "
                    f"Status: {response.status_code} - "
                    f"Duration: {duration:.4f}s"
                )
                
                return response
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"API {request.method} {request.path} failed after {duration:.4f}s: {e}",
                    exc_info=True
                )
                
                if settings.DEBUG_ENABLED:
                    return JsonResponse({
                        'error': str(e),
                        'traceback': traceback.format_exc().split('\n')
                    }, status=500)
                raise
        
        return wrapper
    return decorator


def cache_debug(cache_key_func=None):
    """
    Decorator to debug cache operations.
    
    Args:
        cache_key_func: Function to generate cache key from function args
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(f"cache.{func.__name__}", 'cache')
            
            cache_key = cache_key_func(*args, **kwargs) if cache_key_func else f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            logger.debug(f"Cache operation for {func.__name__} with key: {cache_key}")
            
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.debug(f"Cache operation completed in {duration:.4f}s")
            
            return result
        
        return wrapper
    return decorator
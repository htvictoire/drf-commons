"""
Performance monitoring decorators for API timing analysis.
"""

import time
import functools
from ..debug.core.categories import Categories


def api_performance_monitor(threshold=1.0):
    """
    Monitor API endpoint execution time with configurable warning threshold.
    
    Tracks Django view function execution duration and logs warnings for requests
    exceeding the specified threshold. Captures both successful requests
    and exceptions with timing information.
    
    Args:
        threshold (float): Duration in seconds above which to log warnings
        
    Returns:
        Decorated view function with performance monitoring
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            logger = Categories.get_logger(f"performance.{view_func.__name__}", Categories.PERFORMANCE)
            
            start_time = time.time()
            
            try:
                response = view_func(request, *args, **kwargs)
                duration = time.time() - start_time
                
                if duration > threshold:
                    logger.warning(f"Slow API: {request.method} {request.path} - {duration:.4f}s")
                else:
                    logger.info(f"API timing: {request.method} {request.path} - {duration:.4f}s")
                
                return response
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"API failed: {request.method} {request.path} - {duration:.4f}s: {e}")
                raise
        return wrapper
    return decorator
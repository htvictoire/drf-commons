"""
Cache operation decorators for monitoring and debugging cache behavior.
"""

import time
import functools
from ..debug.core.categories import Categories


def cache_debug(cache_key_func=None):
    """
    Log cache operations with timing and key information.
    
    Captures cache function execution with optional custom key generation
    and logs operation duration for cache performance monitoring.
    
    Args:
        cache_key_func (callable): Function to generate cache key from args/kwargs.
                                  If None, generates hash-based key from arguments.
    
    Returns:
        Decorated function with cache operation logging
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = Categories.get_logger(f"cache.{func.__name__}", Categories.CACHE)
            
            cache_key = cache_key_func(*args, **kwargs) if cache_key_func else f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            logger.debug(f"Cache operation for {func.__name__} with key: {cache_key}")
            
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.debug(f"Cache operation completed in {duration:.4f}s")
            
            return result
        return wrapper
    return decorator
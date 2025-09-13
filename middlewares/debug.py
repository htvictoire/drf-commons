"""
Debug middleware with category awareness.
"""

import time
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from common_conf import settings
from ..debug.core.categories import Categories


class DebugMiddleware(MiddlewareMixin):
    """Request/response debugging middleware."""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.logger = Categories.get_logger('middleware.debug', Categories.REQUESTS)
    
    def process_request(self, request):
        """Process incoming request."""
        request._debug_start_time = time.time()
        request._debug_initial_queries = len(connection.queries)
        
        self.logger.info(f"Request started: {request.method} {request.path}")
        self.logger.debug(f"User: {getattr(request.user, 'username', 'Anonymous') if hasattr(request, 'user') else 'Anonymous'}")
        self.logger.debug(f"User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
        self.logger.debug(f"Remote IP: {self.get_client_ip(request)}")
        
        if request.GET:
            self.logger.debug(f"Query params: {dict(request.GET)}")
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing response."""
        if not hasattr(request, '_debug_start_time'):
            return response
        
        duration = time.time() - request._debug_start_time
        query_count = len(connection.queries) - request._debug_initial_queries
        
        self.logger.info(
            f"Request completed: {request.method} {request.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration:.4f}s - "
            f"Queries: {query_count}"
        )
        
        if duration > settings.DEBUG_SLOW_REQUEST_THRESHOLD:
            self.logger.warning(f"Slow request detected: {duration:.4f}s for {request.path}")
        
        if query_count > settings.DEBUG_HIGH_QUERY_COUNT_THRESHOLD:
            self.logger.warning(f"High query count: {query_count} queries for {request.path}")
        
        # Add debug headers only if logging is enabled (not null logger)
        if self.logger is not Categories._null_logger:
            response['X-Debug-Duration'] = f"{duration:.4f}s"
            response['X-Debug-Queries'] = str(query_count)
        
        return response
    
    def process_exception(self, request, exception):
        """Process unhandled exceptions."""
        if not hasattr(request, '_debug_start_time'):
            return None
        
        duration = time.time() - request._debug_start_time
        
        self.logger.error(
            f"Request failed: {request.method} {request.path} - "
            f"Duration: {duration:.4f}s - "
            f"Exception: {str(exception)}",
            exc_info=True
        )
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SQLDebugMiddleware(MiddlewareMixin):
    """SQL query debugging middleware."""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.logger = Categories.get_logger('middleware.sql', Categories.DATABASE)
    
    def process_request(self, request):
        """Reset query tracking."""
        request._sql_debug_initial_queries = len(connection.queries)
        return None
    
    def process_response(self, request, response):
        """Log SQL queries for this request."""
        if not hasattr(request, '_sql_debug_initial_queries'):
            return response
        
        new_queries = connection.queries[request._sql_debug_initial_queries:]
        
        if new_queries:
            total_time = sum(float(query['time']) for query in new_queries)
            
            self.logger.info(
                f"SQL queries for {request.path}: {len(new_queries)} queries, "
                f"total time: {total_time:.4f}s"
            )
            
            for i, query in enumerate(new_queries, 1):
                self.logger.debug(
                    f"Query {i}: {query['sql']} "
                    f"(Time: {query['time']}s)"
                )
            
            slow_queries = [q for q in new_queries if float(q['time']) > settings.DEBUG_SLOW_QUERY_THRESHOLD]
            if slow_queries:
                self.logger.warning(f"Slow queries detected: {len(slow_queries)} queries > {settings.DEBUG_SLOW_QUERY_THRESHOLD}s")
        
        return response


class ProfilerMiddleware(MiddlewareMixin):
    """Performance profiling middleware."""
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.logger = Categories.get_logger('middleware.profiler', Categories.PERFORMANCE)
        self.enabled = (self.logger is not Categories._null_logger and 
                       settings.ENABLE_PROFILER)
    
    def process_request(self, request):
        """Start profiling if enabled."""
        if not self.enabled:
            return None
        
        try:
            import cProfile
            request._profiler = cProfile.Profile()
            request._profiler.enable()
        except ImportError:
            self.logger.warning("cProfile not available for profiling")
        
        return None
    
    def process_response(self, request, response):
        """Stop profiling and log results."""
        if not self.enabled or not hasattr(request, '_profiler'):
            return response
        
        try:
            request._profiler.disable()
            
            import io
            import pstats
            
            s = io.StringIO()
            ps = pstats.Stats(request._profiler, stream=s)
            ps.sort_stats(settings.DEBUG_PROFILER_SORT_METHOD)
            ps.print_stats(settings.DEBUG_PROFILER_TOP_FUNCTIONS)
            
            self.logger.info(f"Profiling results for {request.path}:")
            self.logger.info(s.getvalue())
            
        except Exception as e:
            self.logger.error(f"Error processing profiler results: {e}")
        
        return response
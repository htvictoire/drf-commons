"""
Debug middleware for request/response logging and profiling.
"""

import time
import json
from .. import settings
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from .logger import get_logger


class DebugMiddleware(MiddlewareMixin):
    """
    Middleware to log request/response details and performance metrics.
    Only active when DEBUG=True.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.logger = get_logger('middleware.debug', 'requests')
    
    def process_request(self, request):
        """Process incoming request."""
        if not settings.DEBUG_ENABLED:
            return None
        
        request._debug_start_time = time.time()
        request._debug_initial_queries = len(connection.queries)
        
        # Log request details
        self.logger.info(f"Request started: {request.method} {request.path}")
        self.logger.debug(f"User: {getattr(request.user, 'username', 'Anonymous') if hasattr(request, 'user') else 'Anonymous'}")
        self.logger.debug(f"User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}")
        self.logger.debug(f"Remote IP: {self.get_client_ip(request)}")
        
        # Log query parameters
        if request.GET:
            self.logger.debug(f"Query params: {dict(request.GET)}")
        
        return None
    
    def process_response(self, request, response):
        """Process outgoing response."""
        if not settings.DEBUG_ENABLED or not hasattr(request, '_debug_start_time'):
            return response
        
        # Calculate timing and query stats
        duration = time.time() - request._debug_start_time
        query_count = len(connection.queries) - request._debug_initial_queries
        
        # Log response details
        self.logger.info(
            f"Request completed: {request.method} {request.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration:.4f}s - "
            f"Queries: {query_count}"
        )
        
        # Log slow requests
        if duration > 1.0:  # Requests taking more than 1 second
            self.logger.warning(f"Slow request detected: {duration:.4f}s for {request.path}")
        
        # Log queries with high count
        if query_count > 10:  # More than 10 database queries
            self.logger.warning(f"High query count: {query_count} queries for {request.path}")
        
        # Add debug headers in development
        if settings.DEBUG_ENABLED:
            response['X-Debug-Duration'] = f"{duration:.4f}s"
            response['X-Debug-Queries'] = str(query_count)
        
        return response
    
    def process_exception(self, request, exception):
        """Process unhandled exceptions."""
        if not settings.DEBUG_ENABLED or not hasattr(request, '_debug_start_time'):
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
    """
    Middleware to log SQL queries in detail.
    Only active when DEBUG=True.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.logger = get_logger('middleware.sql', 'sql')
    
    def process_request(self, request):
        """Reset query tracking."""
        if settings.DEBUG_ENABLED:
            request._sql_debug_initial_queries = len(connection.queries)
        return None
    
    def process_response(self, request, response):
        """Log SQL queries for this request."""
        if not settings.DEBUG_ENABLED or not hasattr(request, '_sql_debug_initial_queries'):
            return response
        
        new_queries = connection.queries[request._sql_debug_initial_queries:]
        
        if new_queries:
            total_time = sum(float(query['time']) for query in new_queries)
            
            self.logger.info(
                f"SQL queries for {request.path}: {len(new_queries)} queries, "
                f"total time: {total_time:.4f}s"
            )
            
            # Log individual queries
            for i, query in enumerate(new_queries, 1):
                self.logger.debug(
                    f"Query {i}: {query['sql']} "
                    f"(Time: {query['time']}s)"
                )
            
            # Log slow queries
            slow_queries = [q for q in new_queries if float(q['time']) > 0.1]
            if slow_queries:
                self.logger.warning(f"Slow queries detected: {len(slow_queries)} queries > 0.1s")
        
        return response


class ProfilerMiddleware(MiddlewareMixin):
    """
    Middleware for profiling request performance.
    Only active when DEBUG=True and ENABLE_PROFILER=True.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.logger = get_logger('middleware.profiler', 'profiler')
        self.enabled = settings.DEBUG_ENABLED and settings.ENABLE_PROFILER
    
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
            ps.sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions
            
            self.logger.info(f"Profiling results for {request.path}:")
            self.logger.info(s.getvalue())
            
        except Exception as e:
            self.logger.error(f"Error processing profiler results: {e}")
        
        return response
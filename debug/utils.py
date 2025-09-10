"""
Debug utility functions and helpers.
"""

import json
import pprint
import traceback
from .. import settings
from django.db import connection
from django.core.serializers.json import DjangoJSONEncoder
from .logger import get_logger


def debug_print(*args, **kwargs):
    """
    Print debug information only when DEBUG=True.
    
    Args:
        *args: Arguments to print
        **kwargs: Keyword arguments for print function
    """
    if settings.DEBUG_ENABLED:
        print("[DEBUG]", *args, **kwargs)


def pretty_print_dict(data, title=None):
    """
    Pretty print dictionary or object for debugging.
    
    Args:
        data: Data to print
        title (str): Optional title for the output
    """
    if not settings.DEBUG_ENABLED:
        return
    
    if title:
        print(f"\n=== {title} ===")
    
    if isinstance(data, dict):
        pprint.pprint(data, indent=2, width=120)
    else:
        try:
            # Try to convert to dict if it's a model instance
            if hasattr(data, '__dict__'):
                pprint.pprint(data.__dict__, indent=2, width=120)
            else:
                pprint.pprint(data, indent=2, width=120)
        except:
            print(str(data))
    
    if title:
        print("=" * (len(title) + 8))


def debug_sql_queries(reset=False):
    """
    Print all SQL queries executed so far.
    
    Args:
        reset (bool): Whether to reset the query log after printing
    """
    if not settings.DEBUG_ENABLED:
        return
    
    queries = connection.queries
    
    print(f"\n=== SQL Queries ({len(queries)} total) ===")
    
    total_time = 0
    for i, query in enumerate(queries, 1):
        time_taken = float(query['time'])
        total_time += time_taken
        
        print(f"\nQuery {i} ({time_taken:.4f}s):")
        print(query['sql'])
    
    print(f"\nTotal time: {total_time:.4f}s")
    print("=" * 40)
    
    if reset:
        connection.queries_log.clear()


def capture_request_data(request):
    """
    Capture request data for debugging purposes.
    
    Args:
        request: Django request object
    
    Returns:
        dict: Request data summary
    """
    data = {
        'method': request.method,
        'path': request.path,
        'full_path': request.get_full_path(),
        'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'remote_addr': request.META.get('REMOTE_ADDR', ''),
        'content_type': request.META.get('CONTENT_TYPE', ''),
        'query_params': dict(request.GET),
    }
    
    # Add POST data if present (be careful with sensitive data)
    if request.method == 'POST':
        data['post_data'] = dict(request.POST)
    
    # Add headers (filter sensitive ones)
    headers = {}
    sensitive_headers = ['authorization', 'cookie', 'x-api-key']
    for key, value in request.META.items():
        if key.startswith('HTTP_'):
            header_name = key[5:].lower()
            if header_name not in sensitive_headers:
                headers[header_name] = value
    data['headers'] = headers
    
    return data


def format_traceback(tb=None):
    """
    Format traceback for logging.
    
    Args:
        tb: Traceback object (uses current if None)
    
    Returns:
        str: Formatted traceback
    """
    if tb is None:
        return traceback.format_exc()
    else:
        return ''.join(traceback.format_tb(tb))


def log_model_changes(instance, action='unknown', user=None):
    """
    Log model instance changes for audit trail.
    
    Args:
        instance: Model instance
        action (str): Action performed (create, update, delete)
        user: User performing the action
    """
    logger = get_logger('models.changes', 'models')
    
    model_name = instance.__class__.__name__
    instance_id = getattr(instance, 'pk', 'unknown')
    user_info = str(user) if user else 'system'
    
    logger.info(f"{action.upper()}: {model_name} {instance_id} by {user_info}")
    
    # Log field changes for updates
    if action == 'update' and hasattr(instance, '_state'):
        try:
            # Get original values if available
            if hasattr(instance, '_original_values'):
                changes = {}
                for field in instance._meta.fields:
                    field_name = field.name
                    old_value = instance._original_values.get(field_name)
                    new_value = getattr(instance, field_name)
                    
                    if old_value != new_value:
                        changes[field_name] = {
                            'old': old_value,
                            'new': new_value
                        }
                
                if changes:
                    logger.debug(f"Field changes: {json.dumps(changes, cls=DjangoJSONEncoder)}")
        except Exception as e:
            logger.warning(f"Could not log field changes: {e}")


def debug_cache_operations(cache_key, operation, result=None, duration=None):
    """
    Debug cache operations.
    
    Args:
        cache_key (str): Cache key being operated on
        operation (str): Operation type (get, set, delete, etc.)
        result: Operation result
        duration (float): Operation duration in seconds
    """
    logger = get_logger('cache.operations', 'cache')
    
    message = f"Cache {operation.upper()}: {cache_key}"
    
    if result is not None:
        if operation == 'get':
            message += f" - {'HIT' if result is not None else 'MISS'}"
        else:
            message += f" - Success: {bool(result)}"
    
    if duration:
        message += f" - Duration: {duration:.4f}s"
    
    logger.debug(message)


def profile_function(func):
    """
    Profile a function's performance.
    
    Args:
        func: Function to profile
    
    Returns:
        tuple: (result, profile_stats)
    """
    if not settings.DEBUG_ENABLED:
        return func(), None
    
    try:
        import cProfile
        import pstats
        import io
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = func()
        
        profiler.disable()
        
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats(10)  # Top 10 functions
        
        return result, s.getvalue()
    except ImportError:
        return func(), "Profiling not available (cProfile not installed)"


def memory_usage():
    """
    Get current memory usage information.
    
    Returns:
        dict: Memory usage information
    """
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss,  # Resident Set Size
            'vms': memory_info.vms,  # Virtual Memory Size
            'percent': process.memory_percent(),
            'available': psutil.virtual_memory().available,
        }
    except ImportError:
        return {"error": "psutil not installed"}


def analyze_queryset(queryset, name="QuerySet"):
    """
    Analyze a QuerySet for debugging.
    
    Args:
        queryset: Django QuerySet to analyze
        name (str): Name for logging purposes
    """
    logger = get_logger('queryset.analysis', 'database')
    
    logger.info(f"Analyzing {name}:")
    logger.info(f"Query: {queryset.query}")
    logger.info(f"Count: {queryset.count()}")
    
    if settings.DEBUG_ENABLED:
        # Show first few items
        try:
            items = list(queryset[:5])
            logger.debug(f"Sample items ({len(items)}): {items}")
        except Exception as e:
            logger.warning(f"Could not fetch sample items: {e}")


def debug_context_processor(request):
    """
    Django context processor to add debug information to templates.
    
    Args:
        request: Django request object
    
    Returns:
        dict: Context variables for templates
    """
    if not settings.DEBUG_ENABLED:
        return {}
    
    return {
        'debug_info': {
            'sql_queries': len(connection.queries),
            'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
            'path': request.path,
            'method': request.method,
        }
    }
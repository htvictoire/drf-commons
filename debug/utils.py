"""
Debug utility functions with category awareness.
"""

import json
import pprint
import traceback
from django.db import connection
from django.core.serializers.json import DjangoJSONEncoder
from common_conf import settings
from .core.categories import Categories


def debug_print(*args, category=Categories.ERRORS, **kwargs):
    """
    Print debug information if category is enabled.
    
    Args:
        *args: Arguments to print
        category (str): Debug category to check (defaults to errors)
        **kwargs: Keyword arguments for print function
    """
    logger = Categories.get_logger('debug.print', category)
    if logger is not Categories._null_logger:
        print("[DEBUG]", *args, **kwargs)


def pretty_print_dict(data, title=None, category=Categories.ERRORS):
    """
    Pretty print dictionary or object for debugging.
    
    Args:
        data: Data to print
        title (str, optional): Title for the output
        category (str): Debug category to check (defaults to errors)
    """
    logger = Categories.get_logger('debug.pretty_print', category)
    if logger is Categories._null_logger:
        return
    
    if title:
        print(f"\n=== {title} ===")
    
    if isinstance(data, dict):
        pprint.pprint(data, indent=settings.DEBUG_PRETTY_PRINT_INDENT, width=settings.DEBUG_PRETTY_PRINT_WIDTH)
    else:
        try:
            if hasattr(data, '__dict__'):
                pprint.pprint(data.__dict__, indent=settings.DEBUG_PRETTY_PRINT_INDENT, width=settings.DEBUG_PRETTY_PRINT_WIDTH)
            else:
                pprint.pprint(data, indent=settings.DEBUG_PRETTY_PRINT_INDENT, width=settings.DEBUG_PRETTY_PRINT_WIDTH)
        except Exception:
            print(str(data))
    
    if title:
        print("=" * (len(title) + settings.DEBUG_TITLE_BORDER_PADDING))


def debug_sql_queries(reset=False):
    """Print all SQL queries executed so far."""
    if not Categories.is_enabled(Categories.DATABASE):
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
    print("=" * settings.DEBUG_SQL_BORDER_LENGTH)
    
    if reset:
        connection.queries_log.clear()


def capture_request_data(request):
    """
    Capture request data for debugging purposes.
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
    
    if request.method == 'POST':
        data['post_data'] = dict(request.POST)
    
    # Filter sensitive headers
    headers = {}
    for key, value in request.META.items():
        if key.startswith('HTTP_'):
            header_name = key[len('HTTP_'):].lower()
            if header_name not in settings.DEBUG_SENSITIVE_HEADERS:
                headers[header_name] = value
    data['headers'] = headers
    
    return data


def format_traceback(tb=None):
    """
    Format traceback for logging.
    """
    if tb is None:
        return traceback.format_exc()
    else:
        return ''.join(traceback.format_tb(tb))


def log_model_changes(instance, action='unknown', user=None):
    """Log model instance changes for audit trail."""
    logger = Categories.get_logger(f'{Categories.MODELS}.changes', Categories.MODELS)
    
    model_name = instance.__class__.__name__
    instance_id = getattr(instance, 'pk', 'unknown')
    user_info = str(user) if user else 'system'
    
    logger.info(f"{action.upper()}: {model_name} {instance_id} by {user_info}")
    
    # Log field changes for updates
    if action == 'update' and hasattr(instance, '_state'):
        try:
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
    """Debug cache operations."""
    logger = Categories.get_logger(f'{Categories.CACHE}.operations', Categories.CACHE)
    
    message = f"Cache {operation.upper()}: {cache_key}"
    
    if result is not None:
        if operation == 'get':
            message += " - HIT"
        else:
            message += f" - Success: {bool(result)}"
    elif operation == 'get':
        message += " - MISS"
    
    if duration:
        message += f" - Duration: {duration:.4f}s"
    
    logger.debug(message)


def profile_function(func):
    """Profile a function's performance."""
    if not Categories.is_enabled(Categories.PERFORMANCE):
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
        ps.sort_stats(settings.DEBUG_PROFILER_SORT_METHOD)
        ps.print_stats(settings.DEBUG_PROFILER_TOP_FUNCTIONS)
        
        return result, s.getvalue()
    except Exception as e:
        return func(), f"Profiling failed: {e}"


def memory_usage():
    """
    Get current memory usage information.
    """
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss': memory_info.rss,
            'vms': memory_info.vms,
            'percent': process.memory_percent(),
            'available': psutil.virtual_memory().available,
        }
    except ImportError:
        return {"error": "psutil not installed"}


def analyze_queryset(queryset, name="QuerySet"):
    """Analyze a QuerySet for debugging."""
    logger = Categories.get_logger('queryset.analysis', Categories.DATABASE)
    
    logger.info(f"Analyzing {name}:")
    logger.info(f"Query: {queryset.query}")
    logger.info(f"Count: {queryset.count()}")
    
    # Show sample items if logger is active (category enabled)
    if logger is not Categories._null_logger:
        try:
            items = list(queryset[:settings.DEBUG_QUERYSET_SAMPLE_SIZE])
            logger.debug(f"Sample items ({len(items)}): {items}")
        except Exception as e:
            logger.warning(f"Could not fetch sample items: {e}")


def debug_context_processor(request, category=Categories.REQUESTS):
    """
    Django context processor to add debug information to templates.
    
    Args:
        request: Django request object
        category (str): Debug category to check (defaults to requests)
    
    Returns:
        dict: Context variables for templates
    """
    logger = Categories.get_logger('debug.context_processor', category)
    if logger is Categories._null_logger:
        return {}
    
    return {
        'debug_info': {
            'sql_queries': len(connection.queries),
            'user': str(request.user) if hasattr(request, 'user') else 'Anonymous',
            'path': request.path,
            'method': request.method,
        }
    }
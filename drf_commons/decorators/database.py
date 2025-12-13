"""
Database query monitoring decorators for performance analysis.
"""

import functools
import time

from django.db import connection

from drf_commons.debug.core.categories import Categories


def log_db_query(query_type=""):
    """
    Monitor database queries and execution time for functions.

    Tracks database queries generated during function execution,
    logging query count, total time, and individual query details.

    Args:
        query_type (str): Descriptive label for database operation type

    Returns:
        Decorated function with database query monitoring
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = Categories.get_logger("database.queries", Categories.DATABASE)

            initial_queries = len(connection.queries)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                new_queries = len(connection.queries) - initial_queries

                logger.info(
                    f"{query_type} {func.__name__}: {new_queries} queries in {execution_time:.4f}s"
                )

                for query in connection.queries[initial_queries:]:
                    logger.debug(f"SQL: {query['sql']} (Time: {query['time']}s)")

                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"{query_type} {func.__name__} failed after {execution_time:.4f}s: {e}"
                )
                raise

        return wrapper

    return decorator

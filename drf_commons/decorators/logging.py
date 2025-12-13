"""
Logging decorators for function calls, exceptions, and API requests.
"""

import functools
import time

from drf_commons.debug.core.categories import Categories


def api_request_logger(log_body=False, log_headers=False):
    """
    Log API request and response details.

    Captures HTTP method, path, query parameters, headers, request body,
    and response status code.

    Args:
        log_body (bool): Include request body in debug logs
        log_headers (bool): Include request headers in debug logs

    Returns:
        Decorated view function with request/response logging
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            logger = Categories.get_logger(f"api.{view_func.__name__}", Categories.API)

            logger.info(f"API {request.method} {request.path}")

            if log_headers:
                logger.debug(f"Headers: {dict(request.headers)}")

            logger.debug(f"Query params: {dict(request.GET)}")

            if log_body and hasattr(request, "body"):
                try:
                    logger.debug(f"Request body: {request.body.decode('utf-8')}")
                except (UnicodeDecodeError, AttributeError):
                    logger.debug("Request body: <binary data>")

            response = view_func(request, *args, **kwargs)

            logger.info(
                f"API {request.method} {request.path} - Status: {response.status_code}"
            )

            return response

        return wrapper

    return decorator


def log_function_call(
    logger_name=None, log_args=True, log_result=True, category=Categories.PERFORMANCE
):
    """
    Log function invocation details with execution timing.

    Records function calls with optional argument capture, return values,
    and execution duration for debugging function behavior.

    Args:
        logger_name (str): Custom logger name. If None, uses module.function_name
        log_args (bool): Include function arguments in logs
        log_result (bool): Include function return value in logs
        category (str): Debug category for conditional logging

    Returns:
        Decorated function with call logging
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = Categories.get_logger(
                logger_name or f"{func.__module__}.{func.__name__}", category
            )

            if log_args:
                logger.debug(
                    f"Calling {func.__name__} with args={args}, kwargs={kwargs}"
                )
            else:
                logger.debug(f"Calling {func.__name__}")

            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                if log_result:
                    logger.debug(
                        f"{func.__name__} completed in {execution_time:.4f}s, result={result}"
                    )
                else:
                    logger.debug(f"{func.__name__} completed in {execution_time:.4f}s")

                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    f"{func.__name__} failed after {execution_time:.4f}s with error: {e}"
                )
                raise

        return wrapper

    return decorator


def log_exceptions(logger_name=None, reraise=True):
    """
    Log function exceptions with context information.

    Captures exception details, function arguments, and stack traces
    with option to suppress exception propagation.

    Args:
        logger_name (str): Custom logger name. If None, uses errors.function_name
        reraise (bool): Whether to re-raise caught exceptions. If False, returns None.

    Returns:
        Decorated function with exception logging
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = Categories.get_logger(
                logger_name or f"errors.{func.__name__}", Categories.ERRORS
            )

            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Exception in {func.__name__}: {e}",
                    exc_info=True,
                    extra={
                        "function": func.__name__,
                        "args": str(args),
                        "kwargs": str(kwargs),
                        "exception_type": type(e).__name__,
                    },
                )

                if reraise:
                    raise
                return None

        return wrapper

    return decorator

"""
Logging decorators for function calls, exceptions, and API requests.
"""

import functools
import json
import time

from drf_commons.debug.core.categories import Categories

REDACTED_VALUE = "***REDACTED***"
DEFAULT_HEADER_REDACT_KEYS = {
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
}
DEFAULT_BODY_REDACT_KEYS = {
    "password",
    "passwd",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "api_key",
    "apikey",
    "client_secret",
}
DEFAULT_MAX_BODY_LENGTH = 2048


def _normalize_key_set(values):
    """Normalize key names for case-insensitive matching."""
    normalized = set()
    for value in values or []:
        key = str(value).strip().lower()
        if key:
            normalized.add(key)
    return normalized


def _truncate_text(value, max_length):
    """Truncate long log payloads to keep logs bounded."""
    if max_length is None or len(value) <= max_length:
        return value
    overflow = len(value) - max_length
    return f"{value[:max_length]}... <truncated {overflow} chars>"


def _redact_json_payload(payload, redacted_keys):
    """Recursively redact sensitive keys from JSON-like payloads."""
    if isinstance(payload, dict):
        redacted = {}
        for key, value in payload.items():
            if str(key).lower() in redacted_keys:
                redacted[key] = REDACTED_VALUE
            else:
                redacted[key] = _redact_json_payload(value, redacted_keys)
        return redacted

    if isinstance(payload, list):
        return [_redact_json_payload(item, redacted_keys) for item in payload]

    return payload


def _sanitize_headers(headers, redacted_headers=None, header_allowlist=None):
    """Sanitize request headers using allowlist and denylist controls."""
    header_map = dict(headers or {})
    redacted_keys = DEFAULT_HEADER_REDACT_KEYS | _normalize_key_set(redacted_headers)
    allowlist = _normalize_key_set(header_allowlist)
    use_allowlist = bool(allowlist)
    sanitized = {}

    for key, value in header_map.items():
        key_lower = str(key).lower()
        if use_allowlist and key_lower not in allowlist:
            continue
        sanitized[key] = REDACTED_VALUE if key_lower in redacted_keys else value

    return sanitized


def _sanitize_request_body(
    request, redacted_body_keys=None, max_body_length=DEFAULT_MAX_BODY_LENGTH
):
    """Sanitize request body with JSON key redaction and size truncation."""
    if not hasattr(request, "body"):
        return "<body unavailable>"

    raw_body = request.body
    if not raw_body:
        return ""

    if isinstance(raw_body, (bytes, bytearray)):
        try:
            raw_text = raw_body.decode("utf-8")
        except UnicodeDecodeError:
            return "<binary data>"
    else:
        raw_text = str(raw_body)

    redacted_keys = DEFAULT_BODY_REDACT_KEYS | _normalize_key_set(redacted_body_keys)
    try:
        parsed_body = json.loads(raw_text)
    except (TypeError, ValueError):
        return "<non-json payload redacted>"

    sanitized = _redact_json_payload(parsed_body, redacted_keys)
    rendered = json.dumps(sanitized, ensure_ascii=False)
    return _truncate_text(rendered, max_body_length)


def api_request_logger(
    log_body=False,
    log_headers=False,
    *,
    redacted_headers=None,
    header_allowlist=None,
    redacted_body_keys=None,
    max_body_length=DEFAULT_MAX_BODY_LENGTH,
    sanitizer_hook=None,
):
    """
    Log API request and response details.

    Captures HTTP method, path, query parameters, headers, request body,
    and response status code.

    Args:
        log_body (bool): Include request body in debug logs
        log_headers (bool): Include request headers in debug logs
        redacted_headers (Iterable[str]): Additional header names to redact
        header_allowlist (Iterable[str]): Optional header names to include in logs
        redacted_body_keys (Iterable[str]): Additional JSON body keys to redact
        max_body_length (int): Maximum body payload length to log
        sanitizer_hook (callable): Optional hook to override sanitized payloads

    Returns:
        Decorated view function with request/response logging
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            logger = Categories.get_logger(f"api.{view_func.__name__}", Categories.API)

            logger.info(f"API {request.method} {request.path}")

            sanitized_headers = None
            sanitized_body = None

            if log_headers:
                sanitized_headers = _sanitize_headers(
                    request.headers,
                    redacted_headers=redacted_headers,
                    header_allowlist=header_allowlist,
                )

            logger.debug(f"Query params: {dict(request.GET)}")

            if log_body:
                sanitized_body = _sanitize_request_body(
                    request,
                    redacted_body_keys=redacted_body_keys,
                    max_body_length=max_body_length,
                )

            if sanitizer_hook and (log_headers or log_body):
                try:
                    overridden = sanitizer_hook(
                        request=request, headers=sanitized_headers, body=sanitized_body
                    )
                    if isinstance(overridden, dict):
                        sanitized_headers = overridden.get("headers", sanitized_headers)
                        sanitized_body = overridden.get("body", sanitized_body)
                    elif isinstance(overridden, tuple) and len(overridden) == 2:
                        sanitized_headers, sanitized_body = overridden
                except Exception:
                    logger.exception("api_request_logger sanitizer_hook failed")

            if log_headers:
                logger.debug(f"Headers: {sanitized_headers}")

            if log_body:
                logger.debug(f"Request body: {sanitized_body}")

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

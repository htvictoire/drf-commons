"""
Utility functions for creating standardized API responses.

Simple functions that create a base response structure and merge in provided data.
Views handle all business logic, pagination, serialization, etc.
"""

from typing import Any, Dict

from django.utils import timezone

from rest_framework import status
from rest_framework.response import Response


def success_response(
    data: Any = None,
    message: str = "Request successful",
    status_code: int = status.HTTP_200_OK,
    headers: Dict[str, str] = None,
    **kwargs,
) -> Response:
    """
    Create a standardized success response.

    Args:
        data: Response data (already serialized) - can be dict, list, or any serializable type
        message: Success message
        status_code: HTTP status code (default 200)
        **kwargs: Additional fields to merge into data

    Returns:
        DRF Response with standardized structure
    """
    response_data = {
        "message": message,
        "success": True,
        "timestamp": timezone.now().isoformat(),
        "data": {},
    }

    # Standardize payload shape under "data".
    if data is not None:
        if isinstance(data, list):
            response_data["data"] = {"results": data}
        elif isinstance(data, dict):
            response_data["data"] = data
        else:
            response_data["data"] = {"value": data}

    # Merge in any additional fields
    if kwargs:
        response_data["data"].update(kwargs)

    return Response(response_data, status=status_code, headers=headers)


def error_response(
    message: str = "An error occurred",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    errors: Dict[str, Any] = None,
    **kwargs,
) -> Response:
    """
    Create a standardized error response.

    Args:
        message: Error message
        status_code: HTTP status code (default 400)
        errors: Detailed error information
        **kwargs: Additional fields to merge into response under "data"

    Returns:
        DRF Response with standardized structure
    """
    response_data = {
        "success": False,
        "timestamp": timezone.now().isoformat(),
        "message": message,
        "errors": {},
        "data": {},
    }

    if errors:
        response_data["errors"] = errors

    # Merge in any additional fields
    response_data["data"].update(kwargs)

    return Response(response_data, status=status_code)

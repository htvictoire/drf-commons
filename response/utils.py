"""
Utility functions for creating standardized API responses.

Simple functions that create a base response structure and merge in provided data.
Views handle all business logic, pagination, serialization, etc.
"""

from typing import Any, Dict
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone


def success_response(
    data: Any = None,
    message: str = None,
    status_code: int = status.HTTP_200_OK,
    headers: Dict[str, str] = None,
    **kwargs
) -> Response:
    """
    Create a standardized success response.
    
    Args:
        data: Response data (already serialized) - can be dict or any value
        message: Success message
        status_code: HTTP status code (default 200)
        **kwargs: Additional fields to merge into response
        
    Returns:
        DRF Response with standardized structure
    """
    response_data = {
        'success': True,
        'timestamp': timezone.now().isoformat(),
    }
    
    if message:
        response_data['message'] = message
    
    # Merge in the data at the root level
    if data is not None:
        if isinstance(data, dict):
            # If data is a dict, merge its keys directly into response
            response_data['data'] = data
        else:
            # If data is not a dict (list, primitive), put it under 'data'
            response_data['data'] = data

    # Merge in any additional fields
    response_data.update(kwargs)
    
    return Response(response_data, status=status_code, headers=headers)


def error_response(
    message: str = "An error occurred",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    errors: Dict[str, Any] = None,
    **kwargs
) -> Response:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        status_code: HTTP status code (default 400)
        errors: Detailed error information
        **kwargs: Additional fields to merge into response
        
    Returns:
        DRF Response with standardized structure
    """
    response_data = {
        'success': False,
        'timestamp': timezone.now().isoformat(),
        'message': message,
    }
    
    if errors:
        response_data['errors'] = errors
    
    # Merge in any additional fields
    response_data.update(kwargs)
    
    return Response(response_data, status=status_code)


def validation_error_response(
    errors: Dict[str, Any],
    message: str = "Validation failed",
    **kwargs
) -> Response:
    """
    Create a validation error response.
    
    Args:
        errors: Validation error details
        message: Error message
        **kwargs: Additional fields to merge into response
        
    Returns:
        DRF Response with standardized structure
    """
    return error_response(
        message=message,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        errors=errors,
        **kwargs
    )



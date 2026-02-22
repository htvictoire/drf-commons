"""
Response package for consistent API responses.

Simple utility functions that create standardized response structure
and merge in provided data. Views handle all business logic.
"""

from .utils import (
    error_response,
    success_response,
)

__all__ = [
    # Utility functions
    "success_response",
    "error_response",
]

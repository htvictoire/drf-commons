"""
Field operators package.

This package contains operator configurations for all Django field types,
organized by field category for better maintainability.
"""

from .text import get_text_operators, get_email_operators, get_url_operators, get_slug_operators
from .numeric import get_numeric_operators, get_decimal_operators
from .datetime import get_date_operators, get_datetime_operators, get_time_operators
from .special import get_boolean_operators, get_uuid_operators, get_json_operators, get_array_operators
from .related import get_foreignkey_operators, get_manytomany_operators

__all__ = [
    # Text field operators
    'get_text_operators',
    'get_email_operators', 
    'get_url_operators',
    'get_slug_operators',
    
    # Numeric field operators
    'get_numeric_operators',
    'get_decimal_operators',
    
    # Date/time field operators
    'get_date_operators',
    'get_datetime_operators',
    'get_time_operators',
    
    # Special field operators
    'get_boolean_operators',
    'get_uuid_operators',
    'get_json_operators',
    'get_array_operators',
    
    # Related field operators
    'get_foreignkey_operators',
    'get_manytomany_operators',
]
"""
Date range filter for flexible date filtering.
"""

from typing import Dict, Optional, Union
from django_filters import rest_framework as django_filters
from django_filters.constants import EMPTY_VALUES
from rest_framework.exceptions import ValidationError


class DateRangeFilter(django_filters.Filter):
    """
    Enhanced date range filter supporting from/to values with flexible operators.
    
    Supports multiple formats:
    - Single date: "2023-01-01"
    - Date range: "2023-01-01,2023-12-31"
    - From date only: "2023-01-01,"
    - To date only: ",2023-12-31"
    - JSON format: {"from": "2023-01-01", "to": "2023-12-31"}
    """
    
    def filter(self, qs, value):
        """Apply date range filtering."""
        if value in EMPTY_VALUES:
            return qs
        
        try:
            date_range = self._parse_date_range(value)
            return self._apply_date_range(qs, date_range)
        except Exception as e:
            raise ValidationError(f"Invalid date range format: {str(e)}")
    
    def _parse_date_range(self, value: Union[str, Dict]) -> Dict[str, Optional[str]]:
        """
        Parse date range from various input formats.
        
        Returns:
            Dictionary with 'from' and 'to' keys
        """
        if isinstance(value, dict):
            return {
                'from': value.get('from'),
                'to': value.get('to')
            }
        
        if isinstance(value, str):
            # Handle JSON string format
            if value.strip().startswith('{'):
                import json
                parsed = json.loads(value)
                return {
                    'from': parsed.get('from'),
                    'to': parsed.get('to')
                }
            
            # Handle comma-separated format
            if ',' in value:
                parts = value.split(',', 1)
                return {
                    'from': parts[0].strip() if parts[0].strip() else None,
                    'to': parts[1].strip() if parts[1].strip() else None
                }
            
            # Single date value - treat as exact match
            return {
                'from': value.strip(),
                'to': value.strip()
            }
        
        raise ValidationError("Date range must be a string or dictionary")
    
    def _apply_date_range(self, qs, date_range: Dict[str, Optional[str]]):
        """Apply the parsed date range to the queryset."""
        from_date = date_range.get('from')
        to_date = date_range.get('to')
        
        if from_date and to_date:
            # Both dates provided - range filter
            if from_date == to_date:
                # Same date - exact match
                return qs.filter(**{f"{self.field_name}__date": from_date})
            else:
                # Date range
                return qs.filter(
                    **{f"{self.field_name}__date__gte": from_date},
                    **{f"{self.field_name}__date__lte": to_date}
                )
        
        elif from_date:
            # Only from date - greater than or equal
            return qs.filter(**{f"{self.field_name}__date__gte": from_date})
        
        elif to_date:
            # Only to date - less than or equal
            return qs.filter(**{f"{self.field_name}__date__lte": to_date})
        
        # No valid dates provided
        return qs
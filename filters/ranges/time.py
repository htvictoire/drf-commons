"""
Time range filter for flexible time filtering.
"""

from typing import Dict, Optional, Union
from django_filters import rest_framework as django_filters
from django_filters.constants import EMPTY_VALUES
from rest_framework.exceptions import ValidationError


class TimeRangeFilter(django_filters.Filter):
    """
    Enhanced time range filter supporting from/to values with flexible operators.
    
    Supports time ranges for TimeField filtering.
    """
    
    def filter(self, qs, value):
        """Apply time range filtering."""
        if value in EMPTY_VALUES:
            return qs
        
        try:
            time_range = self._parse_time_range(value)
            return self._apply_time_range(qs, time_range)
        except Exception as e:
            raise ValidationError(f"Invalid time range format: {str(e)}")
    
    def _parse_time_range(self, value: Union[str, Dict]) -> Dict[str, Optional[str]]:
        """Parse time range from various input formats."""
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
            
            # Single time value - treat as exact match
            return {
                'from': value.strip(),
                'to': value.strip()
            }
        
        raise ValidationError("Time range must be a string or dictionary")
    
    def _apply_time_range(self, qs, time_range: Dict[str, Optional[str]]):
        """Apply the parsed time range to the queryset."""
        from_time = time_range.get('from')
        to_time = time_range.get('to')
        
        if from_time and to_time:
            # Both times provided
            if from_time == to_time:
                # Same time - exact match
                return qs.filter(**{f"{self.field_name}": from_time})
            else:
                # Time range
                return qs.filter(
                    **{f"{self.field_name}__gte": from_time},
                    **{f"{self.field_name}__lte": to_time}
                )
        
        elif from_time:
            # Only from time - greater than or equal
            return qs.filter(**{f"{self.field_name}__gte": from_time})
        
        elif to_time:
            # Only to time - less than or equal
            return qs.filter(**{f"{self.field_name}__lte": to_time})
        
        # No valid times provided
        return qs
"""
Numeric range filter for flexible numeric filtering.
"""

from typing import Dict, Optional, Union
from django_filters import rest_framework as django_filters
from django_filters.constants import EMPTY_VALUES
from rest_framework.exceptions import ValidationError


class NumericRangeFilter(django_filters.Filter):
    """
    Enhanced numeric range filter supporting from/to values with flexible operators.
    
    Similar to DateRangeFilter but for numeric fields.
    """
    
    def filter(self, qs, value):
        """Apply numeric range filtering."""
        if value in EMPTY_VALUES:
            return qs
        
        try:
            numeric_range = self._parse_numeric_range(value)
            return self._apply_numeric_range(qs, numeric_range)
        except Exception as e:
            raise ValidationError(f"Invalid numeric range format: {str(e)}")
    
    def _parse_numeric_range(self, value: Union[str, Dict]) -> Dict[str, Optional[float]]:
        """Parse numeric range from various input formats."""
        if isinstance(value, dict):
            return {
                'from': float(value['from']) if value.get('from') is not None else None,
                'to': float(value['to']) if value.get('to') is not None else None
            }
        
        if isinstance(value, str):
            # Handle JSON string format
            if value.strip().startswith('{'):
                import json
                parsed = json.loads(value)
                return {
                    'from': float(parsed['from']) if parsed.get('from') is not None else None,
                    'to': float(parsed['to']) if parsed.get('to') is not None else None
                }
            
            # Handle comma-separated format
            if ',' in value:
                parts = value.split(',', 1)
                return {
                    'from': float(parts[0].strip()) if parts[0].strip() else None,
                    'to': float(parts[1].strip()) if parts[1].strip() else None
                }
            
            # Single numeric value - treat as exact match
            num_value = float(value.strip())
            return {
                'from': num_value,
                'to': num_value
            }
        
        raise ValidationError("Numeric range must be a string or dictionary")
    
    def _apply_numeric_range(self, qs, numeric_range: Dict[str, Optional[float]]):
        """Apply the parsed numeric range to the queryset."""
        from_value = numeric_range.get('from')
        to_value = numeric_range.get('to')
        
        if from_value is not None and to_value is not None:
            # Both values provided
            if from_value == to_value:
                # Same value - exact match
                return qs.filter(**{f"{self.field_name}": from_value})
            else:
                # Range
                return qs.filter(
                    **{f"{self.field_name}__gte": from_value},
                    **{f"{self.field_name}__lte": to_value}
                )
        
        elif from_value is not None:
            # Only from value - greater than or equal
            return qs.filter(**{f"{self.field_name}__gte": from_value})
        
        elif to_value is not None:
            # Only to value - less than or equal
            return qs.filter(**{f"{self.field_name}__lte": to_value})
        
        # No valid values provided
        return qs
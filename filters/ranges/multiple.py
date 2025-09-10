"""
Multiple range filter for complex range operations with logical operators.
"""

from typing import Dict, List, Union
from django.db.models import Q
from django_filters import rest_framework as django_filters
from django_filters.constants import EMPTY_VALUES
from rest_framework.exceptions import ValidationError


class MultipleRangeFilter(django_filters.Filter):
    """
    Filter that allows multiple range conditions for the same field with logical operators.
    
    Example:
        ?price__multi_range={"or":[{"from":100,"to":200},{"from":500,"to":1000}]}
        ?age__multi_range={"and":[{"from":18,"to":65},{"from":25,"to":55}]}
    """
    
    def filter(self, qs, value):
        """Apply multiple range filtering with logical operators."""
        if value in EMPTY_VALUES:
            return qs
        
        try:
            multi_range = self._parse_multi_range(value)
            return self._apply_multi_range(qs, multi_range)
        except Exception as e:
            raise ValidationError(f"Invalid multiple range format: {str(e)}")
    
    def _parse_multi_range(self, value: Union[str, Dict]) -> Dict:
        """Parse multiple range expressions."""
        if isinstance(value, str):
            import json
            value = json.loads(value)
        
        if not isinstance(value, dict):
            raise ValidationError("Multiple range filter must be a dictionary")
        
        return value
    
    def _apply_multi_range(self, qs, multi_range: Dict):
        """Apply multiple range conditions with logical operators."""
        if "or" in multi_range:
            return self._apply_or_ranges(qs, multi_range["or"])
        elif "and" in multi_range:
            return self._apply_and_ranges(qs, multi_range["and"])
        else:
            # Single range
            return self._apply_single_range(qs, multi_range)
    
    def _apply_or_ranges(self, qs, ranges: List[Dict]):
        """Apply multiple ranges with OR logic."""
        q_objects = []
        for range_dict in ranges:
            range_q = self._build_range_q(range_dict)
            if range_q:
                q_objects.append(range_q)
        
        if q_objects:
            combined_q = q_objects[0]
            for q_obj in q_objects[1:]:
                combined_q |= q_obj
            return qs.filter(combined_q)
        
        return qs
    
    def _apply_and_ranges(self, qs, ranges: List[Dict]):
        """Apply multiple ranges with AND logic."""
        for range_dict in ranges:
            qs = self._apply_single_range(qs, range_dict)
        return qs
    
    def _apply_single_range(self, qs, range_dict: Dict):
        """Apply a single range condition."""
        from_value = range_dict.get('from')
        to_value = range_dict.get('to')
        
        if from_value is not None and to_value is not None:
            if from_value == to_value:
                return qs.filter(**{f"{self.field_name}": from_value})
            else:
                return qs.filter(
                    **{f"{self.field_name}__gte": from_value},
                    **{f"{self.field_name}__lte": to_value}
                )
        elif from_value is not None:
            return qs.filter(**{f"{self.field_name}__gte": from_value})
        elif to_value is not None:
            return qs.filter(**{f"{self.field_name}__lte": to_value})
        
        return qs
    
    def _build_range_q(self, range_dict: Dict):
        """Build a Q object for a single range."""
        from_value = range_dict.get('from')
        to_value = range_dict.get('to')
        
        if from_value is not None and to_value is not None:
            if from_value == to_value:
                return Q(**{f"{self.field_name}": from_value})
            else:
                return Q(**{f"{self.field_name}__gte": from_value}) & Q(**{f"{self.field_name}__lte": to_value})
        elif from_value is not None:
            return Q(**{f"{self.field_name}__gte": from_value})
        elif to_value is not None:
            return Q(**{f"{self.field_name}__lte": to_value})
        
        return Q()
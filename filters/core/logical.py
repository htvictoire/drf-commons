"""
Logical connector filter for complex query combinations.
"""

from typing import Dict, List, Optional, Any, Union
from django.db.models import Q
from django_filters import rest_framework as django_filters
from django_filters.constants import EMPTY_VALUES
from rest_framework.exceptions import ValidationError

from .types import LogicalOperator


class LogicalFilter(django_filters.Filter):
    """
    A filter that supports logical operations (AND, OR, NOT) on multiple conditions.
    
    This filter accepts a JSON structure or query parameter format that allows
    combining multiple filter conditions with logical operators.
    
    Example usage in URL:
        ?logical={"and": [{"name__icontains": "john"}, {"age__gte": 18}]}
        ?logical={"or": [{"status": "active"}, {"status": "pending"}]}
        ?logical={"not": {"status": "inactive"}}
    """
    
    def filter(self, qs, value):
        """Apply logical filtering to the queryset."""
        if value in EMPTY_VALUES:
            return qs
        
        try:
            # Parse the logical expression
            logical_q = self._parse_logical_expression(value)
            if logical_q and not (hasattr(logical_q, 'children') and not logical_q.children):
                return qs.filter(logical_q)
            return qs
        except Exception as e:
            raise ValidationError(f"Invalid logical filter expression: {str(e)}")
    
    def _parse_logical_expression(self, expression: Union[Dict, str]) -> Optional[Q]:
        """
        Parse a logical expression into a Django Q object.
        
        Args:
            expression: Dictionary or string representing the logical expression
            
        Returns:
            Q object representing the logical condition
        """
        if isinstance(expression, str):
            try:
                import json
                expression = json.loads(expression)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON format in logical filter")
        
        if not isinstance(expression, dict):
            raise ValidationError("Logical filter must be a dictionary")
        
        return self._build_q_object(expression)
    
    def _build_q_object(self, expression: Dict[str, Any]) -> Q:
        """
        Recursively build Q objects from logical expressions.
        
        Args:
            expression: Dictionary representing a logical expression
            
        Returns:
            Q object representing the condition
        """
        if not expression:
            return Q()
        
        # Handle logical operators
        if LogicalOperator.AND.value in expression:
            return self._handle_and_operation(expression[LogicalOperator.AND.value])
        
        elif LogicalOperator.OR.value in expression:
            return self._handle_or_operation(expression[LogicalOperator.OR.value])
        
        elif LogicalOperator.NOT.value in expression:
            return self._handle_not_operation(expression[LogicalOperator.NOT.value])
        
        # Handle direct field filters
        else:
            return self._handle_field_filters(expression)
    
    def _handle_and_operation(self, conditions: List[Dict[str, Any]]) -> Q:
        """Handle AND operations by combining conditions with &."""
        if not isinstance(conditions, list):
            raise ValidationError("AND operation requires a list of conditions")
        
        q_objects = []
        for condition in conditions:
            q_obj = self._build_q_object(condition)
            if q_obj:
                q_objects.append(q_obj)
        
        if not q_objects:
            return Q()
        
        # Combine all Q objects with AND
        result = q_objects[0]
        for q_obj in q_objects[1:]:
            result &= q_obj
        
        return result
    
    def _handle_or_operation(self, conditions: List[Dict[str, Any]]) -> Q:
        """Handle OR operations by combining conditions with |."""
        if not isinstance(conditions, list):
            raise ValidationError("OR operation requires a list of conditions")
        
        q_objects = []
        for condition in conditions:
            q_obj = self._build_q_object(condition)
            if q_obj:
                q_objects.append(q_obj)
        
        if not q_objects:
            return Q()
        
        # Combine all Q objects with OR
        result = q_objects[0]
        for q_obj in q_objects[1:]:
            result |= q_obj
        
        return result
    
    def _handle_not_operation(self, condition: Dict[str, Any]) -> Q:
        """Handle NOT operations by negating the condition."""
        if not isinstance(condition, dict):
            raise ValidationError("NOT operation requires a dictionary condition")
        
        q_obj = self._build_q_object(condition)
        return ~q_obj if q_obj else Q()
    
    def _handle_field_filters(self, filters: Dict[str, Any]) -> Q:
        """
        Handle direct field filters and convert them to Q objects.
        
        Args:
            filters: Dictionary of field filters (e.g., {"name__icontains": "john"})
            
        Returns:
            Q object representing the field conditions
        """
        if not filters:
            return Q()
        
        # Validate that all keys are valid field lookups
        for field_lookup in filters.keys():
            if not self._is_valid_field_lookup(field_lookup):
                raise ValidationError(f"Invalid field lookup: {field_lookup}")
        
        return Q(**filters)
    
    def _is_valid_field_lookup(self, field_lookup: str) -> bool:
        """
        Validate that a field lookup is valid for the model.
        
        This is a basic validation - you might want to enhance this
        to check against actual model fields.
        """
        # Basic validation - field lookups should not contain spaces or special chars
        if not field_lookup.replace('_', '').replace('__', '').isalnum():
            return False
        
        # Check for valid lookup suffixes
        valid_suffixes = [
            'exact', 'iexact', 'contains', 'icontains', 'in', 'gt', 'gte', 'lt', 'lte',
            'startswith', 'istartswith', 'endswith', 'iendswith', 'range', 'date',
            'year', 'month', 'day', 'week', 'week_day', 'quarter', 'time', 'hour',
            'minute', 'second', 'isnull', 'regex', 'iregex'
        ]
        
        parts = field_lookup.split('__')
        if len(parts) == 1 or (len(parts) > 1 and parts[-1] in valid_suffixes):
            return True
       
        return False


class ComplexFilterSet(django_filters.FilterSet):
    """
    Enhanced FilterSet that supports complex logical operations.
    
    This FilterSet includes a logical filter that allows combining
    multiple conditions with AND, OR, and NOT operations.
    """
    
    logical = LogicalFilter(
        label="Logical Filter",
        help_text="Complex logical filter supporting AND, OR, NOT operations"
    )
    
    class Meta:
        abstract = True
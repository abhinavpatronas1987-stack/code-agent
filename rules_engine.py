"""
Rules Engine with support for multiple operators.

Supports:
- equals: exact match
- contains: substring/item membership
- greater_than, less_than, gte, lte: numeric/date comparisons
- regex: pattern matching
- in_list: value in a list of options
- not_equals, not_contains, not_in_list: negated versions
"""

import re
from typing import Any, Dict, List, Union, Callable
from dataclasses import is_dataclass, asdict
from datetime import datetime, date
from enum import Enum


class Operator(str, Enum):
    """Supported operators for rule evaluation."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_THAN_OR_EQUAL = "gte"
    LESS_THAN_OR_EQUAL = "lte"
    REGEX = "regex"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


class Rule:
    """Represents a single rule with field, operator, and value."""
    
    def __init__(self, field: str, operator: Union[Operator, str], value: Any):
        """
        Initialize a rule.
        
        Args:
            field: The field name to check (supports nested fields with dot notation)
            operator: The operator to use for comparison
            value: The value to compare against
        """
        self.field = field
        self.operator = Operator(operator) if isinstance(operator, str) else operator
        self.value = value
    
    def evaluate(self, data: Union[Dict, Any]) -> bool:
        """
        Evaluate the rule against data.
        
        Args:
            data: Dictionary or dataclass instance to evaluate
            
        Returns:
            True if the rule matches, False otherwise
        """
        # Convert dataclass to dict if needed
        if is_dataclass(data):
            data = asdict(data)
        
        # Get the field value (supports nested fields)
        field_value = self._get_field_value(data, self.field)
        
        # Apply the operator
        return self._apply_operator(field_value, self.operator, self.value)
    
    def _get_field_value(self, data: Dict, field: str) -> Any:
        """
        Get field value from data, supporting nested fields with dot notation.
        
        Args:
            data: The data dictionary
            field: Field name (e.g., "user.name" for nested fields)
            
        Returns:
            The field value or None if not found
        """
        keys = field.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif hasattr(value, key):
                value = getattr(value, key)
            else:
                return None
            
            if value is None:
                return None
        
        return value
    
    def _apply_operator(self, field_value: Any, operator: Operator, compare_value: Any) -> bool:
        """
        Apply the operator to compare field_value with compare_value.
        
        Args:
            field_value: The value from the data object
            operator: The operator to apply
            compare_value: The value to compare against
            
        Returns:
            True if the comparison matches, False otherwise
        """
        # Handle None values
        if field_value is None:
            return operator == Operator.EQUALS and compare_value is None
        
        # Operator implementations
        if operator == Operator.EQUALS:
            return field_value == compare_value
        
        elif operator == Operator.NOT_EQUALS:
            return field_value != compare_value
        
        elif operator == Operator.CONTAINS:
            if isinstance(field_value, str):
                return str(compare_value) in field_value
            elif isinstance(field_value, (list, tuple, set)):
                return compare_value in field_value
            elif isinstance(field_value, dict):
                return compare_value in field_value.values()
            return False
        
        elif operator == Operator.NOT_CONTAINS:
            return not self._apply_operator(field_value, Operator.CONTAINS, compare_value)
        
        elif operator == Operator.GREATER_THAN:
            try:
                return field_value > compare_value
            except TypeError:
                return False
        
        elif operator == Operator.LESS_THAN:
            try:
                return field_value < compare_value
            except TypeError:
                return False
        
        elif operator == Operator.GREATER_THAN_OR_EQUAL:
            try:
                return field_value >= compare_value
            except TypeError:
                return False
        
        elif operator == Operator.LESS_THAN_OR_EQUAL:
            try:
                return field_value <= compare_value
            except TypeError:
                return False
        
        elif operator == Operator.REGEX:
            if not isinstance(field_value, str):
                field_value = str(field_value)
            try:
                pattern = re.compile(compare_value)
                return pattern.search(field_value) is not None
            except re.error:
                return False
        
        elif operator == Operator.IN_LIST:
            if not isinstance(compare_value, (list, tuple, set)):
                compare_value = [compare_value]
            return field_value in compare_value
        
        elif operator == Operator.NOT_IN_LIST:
            return not self._apply_operator(field_value, Operator.IN_LIST, compare_value)
        
        return False
    
    def __repr__(self) -> str:
        return f"Rule(field='{self.field}', operator={self.operator.value}, value={self.value!r})"


class RuleSet:
    """A collection of rules with AND/OR logic."""
    
    def __init__(self, rules: List[Rule], logic: str = "AND"):
        """
        Initialize a rule set.
        
        Args:
            rules: List of Rule objects
            logic: "AND" (all rules must match) or "OR" (any rule must match)
        """
        self.rules = rules
        self.logic = logic.upper()
        
        if self.logic not in ("AND", "OR"):
            raise ValueError("Logic must be 'AND' or 'OR'")
    
    def evaluate(self, data: Union[Dict, Any]) -> bool:
        """
        Evaluate all rules against data.
        
        Args:
            data: Dictionary or dataclass instance to evaluate
            
        Returns:
            True if rules match according to logic, False otherwise
        """
        if not self.rules:
            return True
        
        if self.logic == "AND":
            return all(rule.evaluate(data) for rule in self.rules)
        else:  # OR
            return any(rule.evaluate(data) for rule in self.rules)
    
    def __repr__(self) -> str:
        return f"RuleSet(logic={self.logic}, rules={len(self.rules)})"


class RulesEngine:
    """Main rules engine for evaluating complex rule sets."""
    
    def __init__(self):
        """Initialize the rules engine."""
        self.rule_sets: List[RuleSet] = []
    
    def add_rule_set(self, rule_set: RuleSet) -> None:
        """Add a rule set to the engine."""
        self.rule_sets.append(rule_set)
    
    def add_rule(self, field: str, operator: Union[Operator, str], value: Any) -> None:
        """
        Add a single rule as a new rule set.
        
        Args:
            field: The field name to check
            operator: The operator to use
            value: The value to compare against
        """
        rule = Rule(field, operator, value)
        self.add_rule_set(RuleSet([rule]))
    
    def evaluate(self, data: Union[Dict, Any], logic: str = "AND") -> bool:
        """
        Evaluate all rule sets against data.
        
        Args:
            data: Dictionary or dataclass instance to evaluate
            logic: "AND" (all rule sets must match) or "OR" (any rule set must match)
            
        Returns:
            True if rule sets match according to logic, False otherwise
        """
        if not self.rule_sets:
            return True
        
        logic = logic.upper()
        if logic == "AND":
            return all(rule_set.evaluate(data) for rule_set in self.rule_sets)
        else:  # OR
            return any(rule_set.evaluate(data) for rule_set in self.rule_sets)
    
    def filter(self, data_list: List[Union[Dict, Any]], logic: str = "AND") -> List[Union[Dict, Any]]:
        """
        Filter a list of data objects based on rules.
        
        Args:
            data_list: List of dictionaries or dataclass instances
            logic: "AND" or "OR" logic for combining rule sets
            
        Returns:
            Filtered list of data objects that match the rules
        """
        return [data for data in data_list if self.evaluate(data, logic)]
    
    def clear(self) -> None:
        """Clear all rule sets."""
        self.rule_sets.clear()
    
    def __repr__(self) -> str:
        return f"RulesEngine(rule_sets={len(self.rule_sets)})"


# Convenience function for quick rule evaluation
def evaluate_rule(data: Union[Dict, Any], field: str, operator: Union[Operator, str], value: Any) -> bool:
    """
    Quick evaluation of a single rule.
    
    Args:
        data: Dictionary or dataclass instance to evaluate
        field: The field name to check
        operator: The operator to use
        value: The value to compare against
        
    Returns:
        True if the rule matches, False otherwise
    """
    rule = Rule(field, operator, value)
    return rule.evaluate(data)
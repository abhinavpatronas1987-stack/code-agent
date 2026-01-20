"""
Operators module for comparison and filtering operations.

Supports: equals, contains, greater/less than, regex, in-list
"""

import re
from typing import Any, List, Pattern, Union
from enum import Enum
from datetime import datetime


class OperatorType(Enum):
    """Enumeration of supported operator types."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    REGEX = "regex"
    NOT_REGEX = "not_regex"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    BETWEEN = "between"


class Operator:
    """Base class for all operators."""
    
    def __init__(self, operator_type: OperatorType):
        self.operator_type = operator_type
    
    def evaluate(self, value: Any, target: Any) -> bool:
        """
        Evaluate the operator.
        
        Args:
            value: The value to test
            target: The target value to compare against
            
        Returns:
            bool: Result of the comparison
        """
        raise NotImplementedError("Subclasses must implement evaluate()")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"


class EqualsOperator(Operator):
    """Checks if value equals target."""
    
    def __init__(self):
        super().__init__(OperatorType.EQUALS)
    
    def evaluate(self, value: Any, target: Any) -> bool:
        """Check if value equals target."""
        return value == target


class NotEqualsOperator(Operator):
    """Checks if value does not equal target."""
    
    def __init__(self):
        super().__init__(OperatorType.NOT_EQUALS)
    
    def evaluate(self, value: Any, target: Any) -> bool:
        """Check if value does not equal target."""
        return value != target


class ContainsOperator(Operator):
    """Checks if value contains target (for strings, lists, etc.)."""
    
    def __init__(self):
        super().__init__(OperatorType.CONTAINS)
    
    def evaluate(self, value: Any, target: Any) -> bool:
        """Check if value contains target."""
        try:
            return target in value
        except TypeError:
            return False


class NotContainsOperator(Operator):
    """Checks if value does not contain target."""
    
    def __init__(self):
        super().__init__(OperatorType.NOT_CONTAINS)
    
    def evaluate(self, value: Any, target: Any) -> bool:
        """Check if value does not contain target."""
        try:
            return target not in value
        except TypeError:
            return True


class StartsWithOperator(Operator):
    """Checks if string value starts with target."""
    
    def __init__(self):
        super().__init__(OperatorType.STARTS_WITH)
    
    def evaluate(self, value: Any, target: Any) -> bool:
        """Check if value starts with target."""
        try:
            return str(value).startswith(str(target))
        except (AttributeError, TypeError):
            return False


class EndsWithOperator(Operator):
    """Checks if string value ends with target."""
    
    def __init__(self):
        super().__init__(OperatorType.ENDS_WITH)
    
    def evaluate(self, value: Any, target: Any) -> bool:
        """Check if value ends with target."""
        try:
            return str(value).endswith(str(target))
        except (AttributeError, TypeError):
            return False


class GreaterThanOperator(Operator):
    """Checks if value is greater than target."""
    
    def __init__(self):
        super().__init__(OperatorType.GREATER_THAN)
    
    def evaluate(self, value: Any, target: Any) -> bool:
        """Check if value is greater than target."""
        try:
            return value > target
        except TypeError:
            return False


class GreaterThanOrEqualOperator(Operator):
    """Checks if value is greater than or equal to target."""
    
    def __init__(self):
        super().__init__(OperatorType.GREATER_THAN_OR_EQUAL)
    
    def evaluate(self, value: Any, target: Any) -> bool:
        """Check if value is greater than or equal to target."""
        try:
            return value >= target
        except TypeError:
            return False


class LessThanOperator(Operator):
    """Checks if value is less than target."""
    
    def __init__(self):
        super().__init__(OperatorType.LESS_THAN)
    
    def evaluate(self, value: Any, target: Any) -> bool:
        """Check if value is less than target."""
        try:
            return value < target
        except TypeError:
            return False


class LessThanOrEqualOperator(Operator):
    """Checks if value is less than or equal to target."""
    
    def __init__(self):
        super().__init__(OperatorType.LESS_THAN_OR_EQUAL)
    
    def evaluate(self, value: Any, target: Any) -> bool:
        """Check if value is less than or equal to target."""
        try:
            return value <= target
        except TypeError:
            return False


class RegexOperator(Operator):
    """Checks if value matches regex pattern."""
    
    def __init__(self):
        super().__init__(OperatorType.REGEX)
        self._compiled_patterns = {}
    
    def evaluate(self, value: Any, target: Union[str, Pattern]) -> bool:
        """
        Check if value matches regex pattern.
        
        Args:
            value: The value to test
            target: Regex pattern (string or compiled Pattern)
            
        Returns:
            bool: True if pattern matches
        """
        try:
            # Convert value to string
            value_str = str(value)
            
            # Compile pattern if it's a string
            if isinstance(target, str):
                if target not in self._compiled_patterns:
                    self._compiled_patterns[target] = re.compile(target)
                pattern = self._compiled_patterns[target]
            else:
                pattern = target
            
            return bool(pattern.search(value_str))
        except (re.error, TypeError):
            return False


class NotRegexOperator(Operator):
    """Checks if value does not match regex pattern."""
    
    def __init__(self):
        super().__init__(OperatorType.NOT_REGEX)
        self._regex_op = RegexOperator()
    
    def evaluate(self, value: Any, target: Union[str, Pattern]) -> bool:
        """Check if value does not match regex pattern."""
        return not self._regex_op.evaluate(value, target)


class InListOperator(Operator):
    """Checks if value is in a list of targets."""
    
    def __init__(self):
        super().__init__(OperatorType.IN_LIST)
    
    def evaluate(self, value: Any, target: List[Any]) -> bool:
        """
        Check if value is in target list.
        
        Args:
            value: The value to test
            target: List of acceptable values
            
        Returns:
            bool: True if value is in list
        """
        try:
            return value in target
        except TypeError:
            return False


class NotInListOperator(Operator):
    """Checks if value is not in a list of targets."""
    
    def __init__(self):
        super().__init__(OperatorType.NOT_IN_LIST)
    
    def evaluate(self, value: Any, target: List[Any]) -> bool:
        """Check if value is not in target list."""
        try:
            return value not in target
        except TypeError:
            return True


class IsEmptyOperator(Operator):
    """Checks if value is empty (None, empty string, empty list, etc.)."""
    
    def __init__(self):
        super().__init__(OperatorType.IS_EMPTY)
    
    def evaluate(self, value: Any, target: Any = None) -> bool:
        """Check if value is empty."""
        if value is None:
            return True
        if isinstance(value, (str, list, dict, tuple, set)):
            return len(value) == 0
        return False


class IsNotEmptyOperator(Operator):
    """Checks if value is not empty."""
    
    def __init__(self):
        super().__init__(OperatorType.IS_NOT_EMPTY)
        self._is_empty_op = IsEmptyOperator()
    
    def evaluate(self, value: Any, target: Any = None) -> bool:
        """Check if value is not empty."""
        return not self._is_empty_op.evaluate(value, target)


class BetweenOperator(Operator):
    """Checks if value is between two targets (inclusive)."""
    
    def __init__(self):
        super().__init__(OperatorType.BETWEEN)
    
    def evaluate(self, value: Any, target: tuple) -> bool:
        """
        Check if value is between min and max.
        
        Args:
            value: The value to test
            target: Tuple of (min, max)
            
        Returns:
            bool: True if min <= value <= max
        """
        try:
            if not isinstance(target, (tuple, list)) or len(target) != 2:
                return False
            min_val, max_val = target
            return min_val <= value <= max_val
        except TypeError:
            return False


class OperatorFactory:
    """Factory for creating operator instances."""
    
    _operators = {
        OperatorType.EQUALS: EqualsOperator,
        OperatorType.NOT_EQUALS: NotEqualsOperator,
        OperatorType.CONTAINS: ContainsOperator,
        OperatorType.NOT_CONTAINS: NotContainsOperator,
        OperatorType.STARTS_WITH: StartsWithOperator,
        OperatorType.ENDS_WITH: EndsWithOperator,
        OperatorType.GREATER_THAN: GreaterThanOperator,
        OperatorType.GREATER_THAN_OR_EQUAL: GreaterThanOrEqualOperator,
        OperatorType.LESS_THAN: LessThanOperator,
        OperatorType.LESS_THAN_OR_EQUAL: LessThanOrEqualOperator,
        OperatorType.REGEX: RegexOperator,
        OperatorType.NOT_REGEX: NotRegexOperator,
        OperatorType.IN_LIST: InListOperator,
        OperatorType.NOT_IN_LIST: NotInListOperator,
        OperatorType.IS_EMPTY: IsEmptyOperator,
        OperatorType.IS_NOT_EMPTY: IsNotEmptyOperator,
        OperatorType.BETWEEN: BetweenOperator,
    }
    
    @classmethod
    def create(cls, operator_type: Union[OperatorType, str]) -> Operator:
        """
        Create an operator instance.
        
        Args:
            operator_type: Type of operator to create
            
        Returns:
            Operator instance
            
        Raises:
            ValueError: If operator type is not supported
        """
        if isinstance(operator_type, str):
            try:
                operator_type = OperatorType(operator_type)
            except ValueError:
                raise ValueError(f"Unknown operator type: {operator_type}")
        
        operator_class = cls._operators.get(operator_type)
        if not operator_class:
            raise ValueError(f"Unsupported operator type: {operator_type}")
        
        return operator_class()


class Condition:
    """Represents a single condition with field, operator, and value."""
    
    def __init__(self, field: str, operator: Union[OperatorType, str, Operator], value: Any):
        """
        Initialize a condition.
        
        Args:
            field: Field name to evaluate
            operator: Operator type or instance
            value: Value to compare against
        """
        self.field = field
        self.value = value
        
        if isinstance(operator, Operator):
            self.operator = operator
        else:
            self.operator = OperatorFactory.create(operator)
    
    def evaluate(self, data: dict) -> bool:
        """
        Evaluate the condition against data.
        
        Args:
            data: Dictionary containing field values
            
        Returns:
            bool: Result of evaluation
        """
        # Get field value from data (supports nested fields with dot notation)
        field_value = self._get_nested_value(data, self.field)
        return self.operator.evaluate(field_value, self.value)
    
    def _get_nested_value(self, data: dict, field: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = field.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value
    
    def __repr__(self) -> str:
        return f"Condition(field={self.field}, operator={self.operator.operator_type.value}, value={self.value})"


class Filter:
    """Filter with multiple conditions combined with AND/OR logic."""
    
    def __init__(self, conditions: List[Condition] = None, logic: str = "AND"):
        """
        Initialize a filter.
        
        Args:
            conditions: List of conditions
            logic: "AND" or "OR" for combining conditions
        """
        self.conditions = conditions or []
        self.logic = logic.upper()
        
        if self.logic not in ("AND", "OR"):
            raise ValueError("Logic must be 'AND' or 'OR'")
    
    def add_condition(self, field: str, operator: Union[OperatorType, str], value: Any):
        """Add a condition to the filter."""
        condition = Condition(field, operator, value)
        self.conditions.append(condition)
        return self
    
    def evaluate(self, data: dict) -> bool:
        """
        Evaluate all conditions against data.
        
        Args:
            data: Dictionary containing field values
            
        Returns:
            bool: Result based on logic (AND/OR)
        """
        if not self.conditions:
            return True
        
        results = [condition.evaluate(data) for condition in self.conditions]
        
        if self.logic == "AND":
            return all(results)
        else:  # OR
            return any(results)
    
    def filter_list(self, data_list: List[dict]) -> List[dict]:
        """
        Filter a list of dictionaries.
        
        Args:
            data_list: List of dictionaries to filter
            
        Returns:
            List of dictionaries that match the filter
        """
        return [item for item in data_list if self.evaluate(item)]
    
    def __repr__(self) -> str:
        return f"Filter(conditions={len(self.conditions)}, logic={self.logic})"


# Convenience functions for quick operator usage
def equals(value: Any, target: Any) -> bool:
    """Check if value equals target."""
    return EqualsOperator().evaluate(value, target)


def contains(value: Any, target: Any) -> bool:
    """Check if value contains target."""
    return ContainsOperator().evaluate(value, target)


def greater_than(value: Any, target: Any) -> bool:
    """Check if value is greater than target."""
    return GreaterThanOperator().evaluate(value, target)


def less_than(value: Any, target: Any) -> bool:
    """Check if value is less than target."""
    return LessThanOperator().evaluate(value, target)


def regex_match(value: Any, pattern: Union[str, Pattern]) -> bool:
    """Check if value matches regex pattern."""
    return RegexOperator().evaluate(value, pattern)


def in_list(value: Any, target_list: List[Any]) -> bool:
    """Check if value is in target list."""
    return InListOperator().evaluate(value, target_list)
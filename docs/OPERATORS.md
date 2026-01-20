# Operators Module Documentation

The operators module provides a comprehensive set of comparison and filtering operators for data validation, filtering, and querying operations.

## Table of Contents

- [Overview](#overview)
- [Supported Operators](#supported-operators)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Advanced Features](#advanced-features)

## Overview

The operators module supports:

- **Equality operators**: equals, not equals
- **String operators**: contains, starts with, ends with
- **Comparison operators**: greater than, less than, between
- **Pattern matching**: regex, not regex
- **List operations**: in list, not in list
- **Empty checks**: is empty, is not empty

## Supported Operators

| Operator | Type | Description | Example |
|----------|------|-------------|---------|
| `EQUALS` | Equality | Value equals target | `5 == 5` |
| `NOT_EQUALS` | Equality | Value does not equal target | `5 != 6` |
| `CONTAINS` | String/Collection | Value contains target | `"hello" in "hello world"` |
| `NOT_CONTAINS` | String/Collection | Value does not contain target | `"xyz" not in "hello"` |
| `STARTS_WITH` | String | String starts with target | `"hello".startswith("hel")` |
| `ENDS_WITH` | String | String ends with target | `"hello".endswith("lo")` |
| `GREATER_THAN` | Comparison | Value > target | `10 > 5` |
| `GREATER_THAN_OR_EQUAL` | Comparison | Value >= target | `10 >= 10` |
| `LESS_THAN` | Comparison | Value < target | `5 < 10` |
| `LESS_THAN_OR_EQUAL` | Comparison | Value <= target | `5 <= 5` |
| `REGEX` | Pattern | Value matches regex pattern | `"test123" matches r"\d+"` |
| `NOT_REGEX` | Pattern | Value does not match pattern | `"test" not matches r"\d+"` |
| `IN_LIST` | Collection | Value is in list | `2 in [1, 2, 3]` |
| `NOT_IN_LIST` | Collection | Value is not in list | `5 not in [1, 2, 3]` |
| `IS_EMPTY` | Empty Check | Value is empty/None | `"" is empty` |
| `IS_NOT_EMPTY` | Empty Check | Value is not empty | `"hello" is not empty` |
| `BETWEEN` | Range | Value is between min and max | `5 between (1, 10)` |

## Quick Start

### Basic Usage with Convenience Functions

```python
from src.core.operators import equals, contains, greater_than, regex_match, in_list

# Equality check
equals(5, 5)  # True

# String contains
contains("hello world", "world")  # True

# Comparison
greater_than(10, 5)  # True

# Regex matching
regex_match("test123", r"\d+")  # True

# List membership
in_list("apple", ["apple", "banana", "orange"])  # True
```

### Using Operator Classes

```python
from src.core.operators import OperatorFactory, OperatorType

# Create operator using factory
op = OperatorFactory.create(OperatorType.CONTAINS)
result = op.evaluate("hello world", "world")  # True

# Or create directly
from src.core.operators import EqualsOperator
op = EqualsOperator()
result = op.evaluate(5, 5)  # True
```

### Using Conditions

```python
from src.core.operators import Condition, OperatorType

# Create a condition
condition = Condition("age", OperatorType.GREATER_THAN, 18)

# Evaluate against data
user = {"name": "Alice", "age": 25}
result = condition.evaluate(user)  # True
```

### Using Filters

```python
from src.core.operators import Filter, OperatorType

# Create filter with multiple conditions
filter_obj = Filter(logic="AND")
filter_obj.add_condition("age", OperatorType.GREATER_THAN_OR_EQUAL, 18)
filter_obj.add_condition("status", OperatorType.EQUALS, "active")

# Evaluate single item
user = {"age": 25, "status": "active"}
result = filter_obj.evaluate(user)  # True

# Filter a list
users = [
    {"name": "Alice", "age": 25, "status": "active"},
    {"name": "Bob", "age": 17, "status": "active"},
    {"name": "Charlie", "age": 30, "status": "inactive"},
]
filtered = filter_obj.filter_list(users)  # Returns [Alice]
```

## Usage Examples

### Example 1: E-commerce Product Filtering

```python
from src.core.operators import Filter, OperatorType

products = [
    {"name": "Laptop", "price": 999, "category": "electronics", "in_stock": True},
    {"name": "Mouse", "price": 25, "category": "electronics", "in_stock": True},
    {"name": "Desk", "price": 299, "category": "furniture", "in_stock": False},
]

# Find electronics under $100 that are in stock
filter_obj = Filter(logic="AND")
filter_obj.add_condition("category", OperatorType.EQUALS, "electronics")
filter_obj.add_condition("price", OperatorType.LESS_THAN, 100)
filter_obj.add_condition("in_stock", OperatorType.EQUALS, True)

result = filter_obj.filter_list(products)
# Returns: [{"name": "Mouse", ...}]
```

### Example 2: User Access Control

```python
from src.core.operators import Filter, OperatorType

users = [
    {"username": "alice", "role": "admin", "email": "alice@company.com"},
    {"username": "bob", "role": "user", "email": "bob@gmail.com"},
    {"username": "charlie", "role": "moderator", "email": "charlie@company.com"},
]

# Find company employees with elevated privileges
filter_obj = Filter(logic="AND")
filter_obj.add_condition("email", OperatorType.CONTAINS, "company.com")
filter_obj.add_condition("role", OperatorType.IN_LIST, ["admin", "moderator"])

result = filter_obj.filter_list(users)
# Returns: [alice, charlie]
```

### Example 3: Log Analysis

```python
from src.core.operators import Filter, OperatorType

logs = [
    {"level": "ERROR", "message": "Database connection failed"},
    {"level": "INFO", "message": "User logged in"},
    {"level": "ERROR", "message": "API timeout"},
]

# Find all errors containing "failed" or "timeout"
filter_obj = Filter(logic="AND")
filter_obj.add_condition("level", OperatorType.EQUALS, "ERROR")
filter_obj.add_condition("message", OperatorType.REGEX, r"(failed|timeout)")

result = filter_obj.filter_list(logs)
# Returns: [first and third log entries]
```

### Example 4: Email Validation

```python
from src.core.operators import regex_match

email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

regex_match("user@example.com", email_pattern)  # True
regex_match("invalid-email", email_pattern)  # False
```

### Example 5: Nested Field Access

```python
from src.core.operators import Condition, OperatorType

# Access nested fields using dot notation
condition = Condition("user.profile.age", OperatorType.GREATER_THAN, 18)

data = {
    "user": {
        "name": "Alice",
        "profile": {
            "age": 25,
            "city": "New York"
        }
    }
}

result = condition.evaluate(data)  # True
```

## API Reference

### OperatorType Enum

```python
class OperatorType(Enum):
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
```

### OperatorFactory

```python
class OperatorFactory:
    @classmethod
    def create(cls, operator_type: Union[OperatorType, str]) -> Operator:
        """Create an operator instance."""
```

### Condition

```python
class Condition:
    def __init__(self, field: str, operator: Union[OperatorType, str, Operator], value: Any):
        """Initialize a condition."""
    
    def evaluate(self, data: dict) -> bool:
        """Evaluate the condition against data."""
```

### Filter

```python
class Filter:
    def __init__(self, conditions: List[Condition] = None, logic: str = "AND"):
        """Initialize a filter."""
    
    def add_condition(self, field: str, operator: Union[OperatorType, str], value: Any):
        """Add a condition to the filter."""
    
    def evaluate(self, data: dict) -> bool:
        """Evaluate all conditions against data."""
    
    def filter_list(self, data_list: List[dict]) -> List[dict]:
        """Filter a list of dictionaries."""
```

## Advanced Features

### Custom Operator Creation

You can create custom operators by extending the `Operator` base class:

```python
from src.core.operators import Operator, OperatorType

class CustomOperator(Operator):
    def __init__(self):
        super().__init__(OperatorType.CUSTOM)
    
    def evaluate(self, value: Any, target: Any) -> bool:
        # Your custom logic here
        return True
```

### Combining Filters

```python
# Create multiple filters and combine results
filter1 = Filter(logic="AND")
filter1.add_condition("age", OperatorType.GREATER_THAN, 18)

filter2 = Filter(logic="OR")
filter2.add_condition("role", OperatorType.EQUALS, "admin")

# Apply both filters
result1 = filter1.filter_list(data)
result2 = filter2.filter_list(result1)
```

### Regex Pattern Caching

The `RegexOperator` automatically caches compiled patterns for better performance:

```python
from src.core.operators import RegexOperator

op = RegexOperator()
# First call compiles and caches the pattern
op.evaluate("test123", r"\d+")
# Subsequent calls use cached pattern
op.evaluate("test456", r"\d+")
```

### Performance Tips

1. **Use compiled regex patterns** for repeated matching
2. **Create operators once** and reuse them
3. **Use appropriate logic** (AND vs OR) to minimize evaluations
4. **Filter early** - apply most restrictive conditions first

## Testing

Run the test suite:

```bash
pytest tests/test_operators.py -v
```

Run specific test class:

```bash
pytest tests/test_operators.py::TestFilter -v
```

## Examples

See `examples/operators_demo.py` for comprehensive examples including:

- Basic operator usage
- Product filtering
- User access control
- Log analysis
- Email validation
- Advanced regex patterns

Run the demo:

```bash
python examples/operators_demo.py
```

## License

This module is part of the code-agent project.
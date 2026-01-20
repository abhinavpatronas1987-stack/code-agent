"""
Tests for the operators module.
"""

import pytest
import re
from src.core.operators import (
    OperatorType,
    OperatorFactory,
    Condition,
    Filter,
    EqualsOperator,
    NotEqualsOperator,
    ContainsOperator,
    NotContainsOperator,
    StartsWithOperator,
    EndsWithOperator,
    GreaterThanOperator,
    GreaterThanOrEqualOperator,
    LessThanOperator,
    LessThanOrEqualOperator,
    RegexOperator,
    NotRegexOperator,
    InListOperator,
    NotInListOperator,
    IsEmptyOperator,
    IsNotEmptyOperator,
    BetweenOperator,
    equals,
    contains,
    greater_than,
    less_than,
    regex_match,
    in_list,
)


class TestEqualsOperator:
    """Test EqualsOperator."""
    
    def test_equals_numbers(self):
        op = EqualsOperator()
        assert op.evaluate(5, 5) is True
        assert op.evaluate(5, 6) is False
    
    def test_equals_strings(self):
        op = EqualsOperator()
        assert op.evaluate("hello", "hello") is True
        assert op.evaluate("hello", "world") is False
    
    def test_equals_none(self):
        op = EqualsOperator()
        assert op.evaluate(None, None) is True
        assert op.evaluate(None, "value") is False


class TestNotEqualsOperator:
    """Test NotEqualsOperator."""
    
    def test_not_equals(self):
        op = NotEqualsOperator()
        assert op.evaluate(5, 6) is True
        assert op.evaluate(5, 5) is False


class TestContainsOperator:
    """Test ContainsOperator."""
    
    def test_contains_string(self):
        op = ContainsOperator()
        assert op.evaluate("hello world", "world") is True
        assert op.evaluate("hello world", "xyz") is False
    
    def test_contains_list(self):
        op = ContainsOperator()
        assert op.evaluate([1, 2, 3], 2) is True
        assert op.evaluate([1, 2, 3], 5) is False
    
    def test_contains_dict(self):
        op = ContainsOperator()
        assert op.evaluate({"a": 1, "b": 2}, "a") is True
        assert op.evaluate({"a": 1, "b": 2}, "c") is False
    
    def test_contains_invalid(self):
        op = ContainsOperator()
        assert op.evaluate(123, "1") is False


class TestNotContainsOperator:
    """Test NotContainsOperator."""
    
    def test_not_contains(self):
        op = NotContainsOperator()
        assert op.evaluate("hello", "xyz") is True
        assert op.evaluate("hello", "ell") is False


class TestStartsWithOperator:
    """Test StartsWithOperator."""
    
    def test_starts_with(self):
        op = StartsWithOperator()
        assert op.evaluate("hello world", "hello") is True
        assert op.evaluate("hello world", "world") is False
    
    def test_starts_with_number(self):
        op = StartsWithOperator()
        assert op.evaluate(12345, "123") is True


class TestEndsWithOperator:
    """Test EndsWithOperator."""
    
    def test_ends_with(self):
        op = EndsWithOperator()
        assert op.evaluate("hello world", "world") is True
        assert op.evaluate("hello world", "hello") is False


class TestGreaterThanOperator:
    """Test GreaterThanOperator."""
    
    def test_greater_than_numbers(self):
        op = GreaterThanOperator()
        assert op.evaluate(10, 5) is True
        assert op.evaluate(5, 10) is False
        assert op.evaluate(5, 5) is False
    
    def test_greater_than_strings(self):
        op = GreaterThanOperator()
        assert op.evaluate("b", "a") is True
        assert op.evaluate("a", "b") is False


class TestGreaterThanOrEqualOperator:
    """Test GreaterThanOrEqualOperator."""
    
    def test_greater_than_or_equal(self):
        op = GreaterThanOrEqualOperator()
        assert op.evaluate(10, 5) is True
        assert op.evaluate(5, 5) is True
        assert op.evaluate(5, 10) is False


class TestLessThanOperator:
    """Test LessThanOperator."""
    
    def test_less_than(self):
        op = LessThanOperator()
        assert op.evaluate(5, 10) is True
        assert op.evaluate(10, 5) is False
        assert op.evaluate(5, 5) is False


class TestLessThanOrEqualOperator:
    """Test LessThanOrEqualOperator."""
    
    def test_less_than_or_equal(self):
        op = LessThanOrEqualOperator()
        assert op.evaluate(5, 10) is True
        assert op.evaluate(5, 5) is True
        assert op.evaluate(10, 5) is False


class TestRegexOperator:
    """Test RegexOperator."""
    
    def test_regex_match(self):
        op = RegexOperator()
        assert op.evaluate("hello123", r"\d+") is True
        assert op.evaluate("hello", r"\d+") is False
    
    def test_regex_email(self):
        op = RegexOperator()
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        assert op.evaluate("test@example.com", pattern) is True
        assert op.evaluate("invalid-email", pattern) is False
    
    def test_regex_compiled_pattern(self):
        op = RegexOperator()
        pattern = re.compile(r"\d+")
        assert op.evaluate("test123", pattern) is True
    
    def test_regex_caching(self):
        op = RegexOperator()
        pattern = r"\d+"
        op.evaluate("test123", pattern)
        assert pattern in op._compiled_patterns


class TestNotRegexOperator:
    """Test NotRegexOperator."""
    
    def test_not_regex(self):
        op = NotRegexOperator()
        assert op.evaluate("hello", r"\d+") is True
        assert op.evaluate("hello123", r"\d+") is False


class TestInListOperator:
    """Test InListOperator."""
    
    def test_in_list(self):
        op = InListOperator()
        assert op.evaluate(2, [1, 2, 3]) is True
        assert op.evaluate(5, [1, 2, 3]) is False
    
    def test_in_list_strings(self):
        op = InListOperator()
        assert op.evaluate("apple", ["apple", "banana", "orange"]) is True
        assert op.evaluate("grape", ["apple", "banana", "orange"]) is False


class TestNotInListOperator:
    """Test NotInListOperator."""
    
    def test_not_in_list(self):
        op = NotInListOperator()
        assert op.evaluate(5, [1, 2, 3]) is True
        assert op.evaluate(2, [1, 2, 3]) is False


class TestIsEmptyOperator:
    """Test IsEmptyOperator."""
    
    def test_is_empty_none(self):
        op = IsEmptyOperator()
        assert op.evaluate(None) is True
    
    def test_is_empty_string(self):
        op = IsEmptyOperator()
        assert op.evaluate("") is True
        assert op.evaluate("hello") is False
    
    def test_is_empty_list(self):
        op = IsEmptyOperator()
        assert op.evaluate([]) is True
        assert op.evaluate([1, 2]) is False
    
    def test_is_empty_dict(self):
        op = IsEmptyOperator()
        assert op.evaluate({}) is True
        assert op.evaluate({"a": 1}) is False


class TestIsNotEmptyOperator:
    """Test IsNotEmptyOperator."""
    
    def test_is_not_empty(self):
        op = IsNotEmptyOperator()
        assert op.evaluate("hello") is True
        assert op.evaluate("") is False
        assert op.evaluate([1, 2]) is True
        assert op.evaluate([]) is False


class TestBetweenOperator:
    """Test BetweenOperator."""
    
    def test_between_numbers(self):
        op = BetweenOperator()
        assert op.evaluate(5, (1, 10)) is True
        assert op.evaluate(1, (1, 10)) is True
        assert op.evaluate(10, (1, 10)) is True
        assert op.evaluate(0, (1, 10)) is False
        assert op.evaluate(11, (1, 10)) is False
    
    def test_between_strings(self):
        op = BetweenOperator()
        assert op.evaluate("b", ("a", "c")) is True
        assert op.evaluate("d", ("a", "c")) is False
    
    def test_between_invalid_target(self):
        op = BetweenOperator()
        assert op.evaluate(5, (1,)) is False
        assert op.evaluate(5, "invalid") is False


class TestOperatorFactory:
    """Test OperatorFactory."""
    
    def test_create_from_enum(self):
        op = OperatorFactory.create(OperatorType.EQUALS)
        assert isinstance(op, EqualsOperator)
    
    def test_create_from_string(self):
        op = OperatorFactory.create("equals")
        assert isinstance(op, EqualsOperator)
    
    def test_create_all_operators(self):
        for op_type in OperatorType:
            op = OperatorFactory.create(op_type)
            assert op is not None
    
    def test_create_invalid_operator(self):
        with pytest.raises(ValueError):
            OperatorFactory.create("invalid_operator")


class TestCondition:
    """Test Condition class."""
    
    def test_condition_simple(self):
        condition = Condition("age", OperatorType.GREATER_THAN, 18)
        assert condition.evaluate({"age": 25}) is True
        assert condition.evaluate({"age": 15}) is False
    
    def test_condition_nested_field(self):
        condition = Condition("user.age", OperatorType.EQUALS, 30)
        data = {"user": {"age": 30, "name": "John"}}
        assert condition.evaluate(data) is True
    
    def test_condition_string_operator(self):
        condition = Condition("name", "contains", "John")
        assert condition.evaluate({"name": "John Doe"}) is True
    
    def test_condition_operator_instance(self):
        op = EqualsOperator()
        condition = Condition("status", op, "active")
        assert condition.evaluate({"status": "active"}) is True
    
    def test_condition_missing_field(self):
        condition = Condition("missing", OperatorType.EQUALS, "value")
        assert condition.evaluate({"other": "value"}) is False


class TestFilter:
    """Test Filter class."""
    
    def test_filter_and_logic(self):
        filter_obj = Filter(logic="AND")
        filter_obj.add_condition("age", OperatorType.GREATER_THAN, 18)
        filter_obj.add_condition("status", OperatorType.EQUALS, "active")
        
        assert filter_obj.evaluate({"age": 25, "status": "active"}) is True
        assert filter_obj.evaluate({"age": 25, "status": "inactive"}) is False
        assert filter_obj.evaluate({"age": 15, "status": "active"}) is False
    
    def test_filter_or_logic(self):
        filter_obj = Filter(logic="OR")
        filter_obj.add_condition("age", OperatorType.GREATER_THAN, 18)
        filter_obj.add_condition("status", OperatorType.EQUALS, "premium")
        
        assert filter_obj.evaluate({"age": 25, "status": "basic"}) is True
        assert filter_obj.evaluate({"age": 15, "status": "premium"}) is True
        assert filter_obj.evaluate({"age": 15, "status": "basic"}) is False
    
    def test_filter_list(self):
        filter_obj = Filter(logic="AND")
        filter_obj.add_condition("age", OperatorType.GREATER_THAN_OR_EQUAL, 18)
        filter_obj.add_condition("status", OperatorType.EQUALS, "active")
        
        data = [
            {"name": "Alice", "age": 25, "status": "active"},
            {"name": "Bob", "age": 17, "status": "active"},
            {"name": "Charlie", "age": 30, "status": "inactive"},
            {"name": "Diana", "age": 22, "status": "active"},
        ]
        
        result = filter_obj.filter_list(data)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Diana"
    
    def test_filter_empty_conditions(self):
        filter_obj = Filter()
        assert filter_obj.evaluate({"any": "data"}) is True
    
    def test_filter_invalid_logic(self):
        with pytest.raises(ValueError):
            Filter(logic="INVALID")


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_equals_function(self):
        assert equals(5, 5) is True
        assert equals(5, 6) is False
    
    def test_contains_function(self):
        assert contains("hello world", "world") is True
        assert contains([1, 2, 3], 2) is True
    
    def test_greater_than_function(self):
        assert greater_than(10, 5) is True
        assert greater_than(5, 10) is False
    
    def test_less_than_function(self):
        assert less_than(5, 10) is True
        assert less_than(10, 5) is False
    
    def test_regex_match_function(self):
        assert regex_match("test123", r"\d+") is True
        assert regex_match("test", r"\d+") is False
    
    def test_in_list_function(self):
        assert in_list(2, [1, 2, 3]) is True
        assert in_list(5, [1, 2, 3]) is False


class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    def test_user_filtering(self):
        """Test filtering users by multiple criteria."""
        users = [
            {"name": "Alice", "age": 25, "email": "alice@example.com", "role": "admin"},
            {"name": "Bob", "age": 17, "email": "bob@example.com", "role": "user"},
            {"name": "Charlie", "age": 30, "email": "charlie@test.com", "role": "user"},
            {"name": "Diana", "age": 22, "email": "diana@example.com", "role": "moderator"},
        ]
        
        # Filter: age >= 18 AND email contains "example.com"
        filter_obj = Filter(logic="AND")
        filter_obj.add_condition("age", OperatorType.GREATER_THAN_OR_EQUAL, 18)
        filter_obj.add_condition("email", OperatorType.CONTAINS, "example.com")
        
        result = filter_obj.filter_list(users)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Diana"
    
    def test_product_search(self):
        """Test filtering products."""
        products = [
            {"name": "Laptop", "price": 999, "category": "electronics", "in_stock": True},
            {"name": "Mouse", "price": 25, "category": "electronics", "in_stock": True},
            {"name": "Desk", "price": 299, "category": "furniture", "in_stock": False},
            {"name": "Chair", "price": 199, "category": "furniture", "in_stock": True},
        ]
        
        # Filter: price between 50 and 500 AND in_stock = True
        filter_obj = Filter(logic="AND")
        filter_obj.add_condition("price", OperatorType.BETWEEN, (50, 500))
        filter_obj.add_condition("in_stock", OperatorType.EQUALS, True)
        
        result = filter_obj.filter_list(products)
        assert len(result) == 1
        assert result[0]["name"] == "Chair"
    
    def test_log_filtering(self):
        """Test filtering log entries."""
        logs = [
            {"level": "ERROR", "message": "Database connection failed", "timestamp": 1000},
            {"level": "INFO", "message": "User logged in", "timestamp": 2000},
            {"level": "WARNING", "message": "High memory usage", "timestamp": 3000},
            {"level": "ERROR", "message": "API timeout", "timestamp": 4000},
        ]
        
        # Filter: level in ["ERROR", "WARNING"] OR message contains "timeout"
        filter_obj = Filter(logic="OR")
        filter_obj.add_condition("level", OperatorType.IN_LIST, ["ERROR", "WARNING"])
        filter_obj.add_condition("message", OperatorType.REGEX, r"timeout")
        
        result = filter_obj.filter_list(logs)
        assert len(result) == 3
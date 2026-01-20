"""
Unit tests for the Rules Engine.
"""

import unittest
from dataclasses import dataclass
from datetime import date
from rules_engine import Rule, RuleSet, RulesEngine, Operator, evaluate_rule


class TestRule(unittest.TestCase):
    """Test cases for the Rule class."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com",
            "role": "admin",
            "tags": ["premium", "verified"],
            "score": 85.5
        }
    
    def test_equals_operator(self):
        """Test equals operator."""
        rule = Rule("role", Operator.EQUALS, "admin")
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("role", Operator.EQUALS, "user")
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_not_equals_operator(self):
        """Test not_equals operator."""
        rule = Rule("role", Operator.NOT_EQUALS, "user")
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("role", Operator.NOT_EQUALS, "admin")
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_contains_operator_string(self):
        """Test contains operator with strings."""
        rule = Rule("email", Operator.CONTAINS, "example")
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("email", Operator.CONTAINS, "gmail")
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_contains_operator_list(self):
        """Test contains operator with lists."""
        rule = Rule("tags", Operator.CONTAINS, "premium")
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("tags", Operator.CONTAINS, "basic")
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_not_contains_operator(self):
        """Test not_contains operator."""
        rule = Rule("tags", Operator.NOT_CONTAINS, "basic")
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("tags", Operator.NOT_CONTAINS, "premium")
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_greater_than_operator(self):
        """Test greater_than operator."""
        rule = Rule("age", Operator.GREATER_THAN, 25)
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("age", Operator.GREATER_THAN, 35)
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_less_than_operator(self):
        """Test less_than operator."""
        rule = Rule("age", Operator.LESS_THAN, 35)
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("age", Operator.LESS_THAN, 25)
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_gte_operator(self):
        """Test greater_than_or_equal operator."""
        rule = Rule("age", Operator.GREATER_THAN_OR_EQUAL, 30)
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("age", Operator.GREATER_THAN_OR_EQUAL, 31)
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_lte_operator(self):
        """Test less_than_or_equal operator."""
        rule = Rule("age", Operator.LESS_THAN_OR_EQUAL, 30)
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("age", Operator.LESS_THAN_OR_EQUAL, 29)
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_regex_operator(self):
        """Test regex operator."""
        rule = Rule("email", Operator.REGEX, r"^[\w\.-]+@[\w\.-]+\.\w+$")
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("email", Operator.REGEX, r"@gmail\.com$")
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_in_list_operator(self):
        """Test in_list operator."""
        rule = Rule("role", Operator.IN_LIST, ["admin", "moderator"])
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("role", Operator.IN_LIST, ["user", "guest"])
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_not_in_list_operator(self):
        """Test not_in_list operator."""
        rule = Rule("role", Operator.NOT_IN_LIST, ["user", "guest"])
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("role", Operator.NOT_IN_LIST, ["admin", "moderator"])
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_nested_fields(self):
        """Test nested field access with dot notation."""
        nested_data = {
            "user": {
                "profile": {
                    "name": "Alice"
                }
            }
        }
        
        rule = Rule("user.profile.name", Operator.EQUALS, "Alice")
        self.assertTrue(rule.evaluate(nested_data))
        
        rule = Rule("user.profile.name", Operator.EQUALS, "Bob")
        self.assertFalse(rule.evaluate(nested_data))
    
    def test_none_values(self):
        """Test handling of None values."""
        data = {"field": None}
        
        rule = Rule("field", Operator.EQUALS, None)
        self.assertTrue(rule.evaluate(data))
        
        rule = Rule("field", Operator.EQUALS, "value")
        self.assertFalse(rule.evaluate(data))
    
    def test_missing_fields(self):
        """Test handling of missing fields."""
        rule = Rule("missing_field", Operator.EQUALS, "value")
        self.assertFalse(rule.evaluate(self.test_data))
    
    def test_float_comparisons(self):
        """Test comparisons with float values."""
        rule = Rule("score", Operator.GREATER_THAN, 80.0)
        self.assertTrue(rule.evaluate(self.test_data))
        
        rule = Rule("score", Operator.LESS_THAN_OR_EQUAL, 85.5)
        self.assertTrue(rule.evaluate(self.test_data))


class TestRuleWithDataclass(unittest.TestCase):
    """Test Rule with dataclass objects."""
    
    def setUp(self):
        """Set up test dataclass."""
        @dataclass
        class User:
            name: str
            age: int
            role: str
        
        self.User = User
        self.user = User(name="Alice", age=25, role="admin")
    
    def test_dataclass_evaluation(self):
        """Test rule evaluation with dataclass."""
        rule = Rule("name", Operator.EQUALS, "Alice")
        self.assertTrue(rule.evaluate(self.user))
        
        rule = Rule("age", Operator.GREATER_THAN, 20)
        self.assertTrue(rule.evaluate(self.user))


class TestRuleSet(unittest.TestCase):
    """Test cases for the RuleSet class."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data = {
            "age": 30,
            "role": "admin",
            "email": "test@example.com"
        }
    
    def test_and_logic_all_match(self):
        """Test AND logic when all rules match."""
        rule_set = RuleSet([
            Rule("age", Operator.GREATER_THAN, 18),
            Rule("role", Operator.EQUALS, "admin")
        ], logic="AND")
        
        self.assertTrue(rule_set.evaluate(self.test_data))
    
    def test_and_logic_one_fails(self):
        """Test AND logic when one rule fails."""
        rule_set = RuleSet([
            Rule("age", Operator.GREATER_THAN, 18),
            Rule("role", Operator.EQUALS, "user")
        ], logic="AND")
        
        self.assertFalse(rule_set.evaluate(self.test_data))
    
    def test_or_logic_one_matches(self):
        """Test OR logic when one rule matches."""
        rule_set = RuleSet([
            Rule("age", Operator.LESS_THAN, 18),
            Rule("role", Operator.EQUALS, "admin")
        ], logic="OR")
        
        self.assertTrue(rule_set.evaluate(self.test_data))
    
    def test_or_logic_none_match(self):
        """Test OR logic when no rules match."""
        rule_set = RuleSet([
            Rule("age", Operator.LESS_THAN, 18),
            Rule("role", Operator.EQUALS, "user")
        ], logic="OR")
        
        self.assertFalse(rule_set.evaluate(self.test_data))
    
    def test_empty_rule_set(self):
        """Test empty rule set."""
        rule_set = RuleSet([], logic="AND")
        self.assertTrue(rule_set.evaluate(self.test_data))
    
    def test_invalid_logic(self):
        """Test invalid logic raises error."""
        with self.assertRaises(ValueError):
            RuleSet([Rule("age", Operator.EQUALS, 30)], logic="INVALID")


class TestRulesEngine(unittest.TestCase):
    """Test cases for the RulesEngine class."""
    
    def setUp(self):
        """Set up test data and engine."""
        self.engine = RulesEngine()
        self.test_data = {
            "age": 30,
            "role": "admin",
            "score": 85
        }
    
    def test_add_rule_set(self):
        """Test adding rule sets."""
        rule_set = RuleSet([Rule("age", Operator.GREATER_THAN, 18)])
        self.engine.add_rule_set(rule_set)
        
        self.assertEqual(len(self.engine.rule_sets), 1)
    
    def test_add_rule(self):
        """Test adding a single rule."""
        self.engine.add_rule("age", Operator.GREATER_THAN, 18)
        
        self.assertEqual(len(self.engine.rule_sets), 1)
        self.assertTrue(self.engine.evaluate(self.test_data))
    
    def test_evaluate_and_logic(self):
        """Test evaluation with AND logic."""
        self.engine.add_rule_set(RuleSet([Rule("age", Operator.GREATER_THAN, 18)]))
        self.engine.add_rule_set(RuleSet([Rule("role", Operator.EQUALS, "admin")]))
        
        self.assertTrue(self.engine.evaluate(self.test_data, logic="AND"))
    
    def test_evaluate_or_logic(self):
        """Test evaluation with OR logic."""
        self.engine.add_rule_set(RuleSet([Rule("age", Operator.LESS_THAN, 18)]))
        self.engine.add_rule_set(RuleSet([Rule("role", Operator.EQUALS, "admin")]))
        
        self.assertTrue(self.engine.evaluate(self.test_data, logic="OR"))
    
    def test_filter(self):
        """Test filtering a list of data."""
        data_list = [
            {"age": 25, "role": "admin"},
            {"age": 17, "role": "user"},
            {"age": 30, "role": "user"},
        ]
        
        self.engine.add_rule_set(RuleSet([
            Rule("age", Operator.GREATER_THAN_OR_EQUAL, 18)
        ]))
        
        filtered = self.engine.filter(data_list)
        self.assertEqual(len(filtered), 2)
    
    def test_clear(self):
        """Test clearing rule sets."""
        self.engine.add_rule("age", Operator.GREATER_THAN, 18)
        self.engine.clear()
        
        self.assertEqual(len(self.engine.rule_sets), 0)
    
    def test_empty_engine(self):
        """Test empty engine evaluation."""
        self.assertTrue(self.engine.evaluate(self.test_data))


class TestQuickEvaluation(unittest.TestCase):
    """Test the quick evaluation helper function."""
    
    def test_evaluate_rule_function(self):
        """Test the evaluate_rule helper function."""
        data = {"score": 85}
        
        result = evaluate_rule(data, "score", Operator.GREATER_THAN, 80)
        self.assertTrue(result)
        
        result = evaluate_rule(data, "score", Operator.LESS_THAN, 80)
        self.assertFalse(result)


class TestDateComparisons(unittest.TestCase):
    """Test date and datetime comparisons."""
    
    def test_date_comparisons(self):
        """Test comparison operators with dates."""
        data = {
            "start_date": date(2026, 1, 1),
            "end_date": date(2026, 12, 31)
        }
        
        rule = Rule("start_date", Operator.LESS_THAN, date(2026, 6, 1))
        self.assertTrue(rule.evaluate(data))
        
        rule = Rule("end_date", Operator.GREATER_THAN, date(2026, 6, 1))
        self.assertTrue(rule.evaluate(data))


if __name__ == "__main__":
    unittest.main()
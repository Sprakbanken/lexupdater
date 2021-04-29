"""
Test suite for all the classes in the dialect_updater.py module
"""
from unittest.mock import patch

import pytest

from lexupdater import dialect_updater


@pytest.fixture
def rule_dict():
    """A test example of a structured rule from a ruleset"""
    const = {"field": "field", "pattern": "const_pattern", "is_regex": "bool"}
    rule = {"pattern": "pattern", "repl": "repl", "constraints": [const]}
    top = {"areas": ["list"], "name": "name", "rules": [rule]}
    return top


class TestValidators:
    """Test validation of rules and blacklists"""

    def test_rule_validator_validate_passing(self, rule_dict):
        # given
        validator = dialect_updater.RuleValidator(rule_dict)
        # when
        validator.validate()
        # then, if no Error is raised, the test passes

    def test_rule_validator_validate_raises_error(self, rule_dict):
        # given
        rule_dict["unexpected_key"] = "unexpected_value"
        validator = dialect_updater.RuleValidator(rule_dict)
        # when
        with pytest.raises(KeyError):
            validator.validate()

    def test_blacklist_validator_validate_raises_error(self):
        # given
        input_dict = {
            "ruleset": "str",
            "words": ["list", "of", "words"],
            "unexpected_key": "unexpected_value",
        }
        validator = dialect_updater.BlacklistValidator(input_dict)
        # when
        with pytest.raises(KeyError):
            validator.validate()

    def test_blacklist_validator_validate_passes(self):
        # given
        blacklist_dict = {
            "ruleset": "str",
            "words": ["list", "of", "words"],
        }
        validator = dialect_updater.BlacklistValidator(blacklist_dict)
        # when
        validator.validate()


class TestQueryBuilders:
    """Test that queries are constructed as intended"""

    def test_query_builder(self, rule_dict):
        # given
        rule = rule_dict["rules"][0]
        # when
        q_builder = dialect_updater.QueryBuilder("area", rule, "word_table")
        # then
        assert isinstance(q_builder, dialect_updater.QueryBuilder)
        assert q_builder._constrained_query  # direct boolean assertion

    def test_update_query_builder(self, rule_dict):
        # given
        rule = rule_dict["rules"][0]
        q_builder = dialect_updater.UpdateQueryBuilder("area", rule, "table")
        # when
        query, values, constrained_bool = q_builder.get_update_query()
        # then
        assert "UPDATE area SET nofabet = REGREPLACE(?,?,nofabet)" in query
        assert "WHERE word_id IN (SELECT word_id FROM table" in query
        assert "WHERE field REGEXP ?" in query
        assert values == ["pattern", "repl", "const_pattern"]
        assert constrained_bool  # bool("bool") Evaluates to True

    @pytest.mark.skip("Not implemented yet")
    def test_select_query_builder(self):
        """Skeleton test for desired functionality"""
        # given
        rule = rule_dict["rules"][0]
        # We don't really need separate classes for these building functions
        q_builder = dialect_updater.QueryBuilder()
        # when
        result_query = q_builder.build_select_query("area", rule, "word_table")
        # then
        # TODO: elaborate on the desired output queries
        assert "SELECT " in result_query
        assert "WHERE " in result_query
        assert rule["pattern"] in result_query


class TestReaders:
    """Test that constraints and blacklists are parsed
    and converted to the expected SQL-query fragments.
    """

    def test_parse_constraints(self):
        # given
        constraints = [
            {"field": "pos", "pattern": r"NN", "is_regex": False},
            {"field": "feats", "pattern": r"MAS", "is_regex": True},
        ]
        # when
        result_string, result_values = dialect_updater.parse_constraints(
            constraints, "word_table"
        )
        # then
        assert result_values == ["NN", "MAS"]
        assert "pos = ? AND feats REGEXP ?" in result_string

    def test_parse_blacklists(self):
        # given
        input_blacklists = {"ruleset": "test", "words": ["garn", "klarne"]}
        # when
        result_string, result_values = dialect_updater.parse_exemptions(
            input_blacklists
        )
        # then
        assert result_string == " wordform NOT IN (?,?)"
        assert result_values == ["garn", "klarne"]

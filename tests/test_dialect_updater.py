"""
Test suite for all the classes in the dialect_updater.py module
"""
from unittest.mock import patch

import pytest

from lexupdater import dialect_updater


@pytest.fixture
def rule():
    """A test example of a structured rule from a ruleset"""
    return {
        "pattern": r"\bAX0 R$",
        "repl": r"AA0 R",
        "constraints": [
            {"field": "pos", "pattern": "NN", "is_regex": False},
            {"field": "feats", "pattern": "MAS", "is_regex": True},
        ],
    }


class TestQueryBuilders:
    """Test that queries are constructed as intended"""

    def test_query_builder(self, rule):
        # when
        q_builder = dialect_updater.QueryBuilder("area", rule, "word_table")
        # then
        assert isinstance(q_builder, dialect_updater.QueryBuilder)
        assert q_builder._constrained_query  # direct boolean assertion

    def test_update_query_builder(self, rule):
        # given
        q_builder = dialect_updater.UpdateQueryBuilder("area", rule, "table")
        # when
        query, values, constrained_bool = q_builder.get_update_query()
        # then
        assert "UPDATE area SET nofabet = REGREPLACE(?,?,nofabet)" in query
        assert "WHERE word_id IN (SELECT word_id FROM table" in query
        assert "WHERE pos = ? AND feats REGEXP ?" in query
        assert values == [
            rule["pattern"],  rule["repl"], "NN", "MAS"
        ]
        assert constrained_bool  # bool("bool") Evaluates to True

    @pytest.mark.skip("Not implemented yet")
    def test_select_query_builder(self, rule):
        """Skeleton test for desired functionality"""
        # given
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

    def test_parse_constraints(self, rule):
        # given
        constraints = rule["constraints"]
        reader = dialect_updater.ConstraintReader(constraints, "word_table")
        # when
        result_string, result_values = reader.get_constraints()
        # then
        assert result_values == ["NN", "MAS"]
        assert "pos = ? AND feats REGEXP ?" in result_string

    def test_parse_blacklists(self):
        # given
        input_blacklists = {"ruleset": "test", "words": ["garn", "klarne"]}
        reader = dialect_updater.BlacklistReader(input_blacklists)
        # when
        result_string, result_values = reader.get_blacklist()
        # then
        assert result_string == " wordform NOT IN (?,?)"
        assert result_values == ["garn", "klarne"]

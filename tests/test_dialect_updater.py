"""
Test suite for all the classes in the dialect_updater.py module
"""

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


def test_parse_constraints(rule):
    # given
    constraints = rule["constraints"]
    # when
    result_string, result_values = dialect_updater.parse_constraints(
        constraints
    )
    # then
    assert result_values == ["NN", "MAS"]
    assert "pos = ? AND feats REGEXP ?" in result_string


def test_parse_constraints_with_empty_input():
    result_string, result_values = dialect_updater.parse_constraints([])
    # then
    assert result_values == []
    assert result_string == ""


@pytest.mark.parametrize(
    "words, expected",
    [
        (["garn", "klarne"], "wordform NOT IN (?,?)"),
        (["1", "2", "3"], "wordform NOT IN (?,?,?)"),
        ([], "")
    ]
)
def test_parse_exemptions(words, expected):
    # when
    result_string = dialect_updater.parse_exemptions(words)
    # then
    assert result_string == expected


def test_map_rule_exemptions():
    # given
    input_exemptions = [{"ruleset": "test", "words": ["garn", "klarne"]}]
    expected = {"test": ["garn", "klarne"]}
    # when
    result = dialect_updater.map_rule_exemptions(input_exemptions)
    # then
    assert list(result.keys()) == list(expected.keys())
    assert list(result.values()) == list(expected.values())

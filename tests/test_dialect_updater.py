"""Test suite for all the classes in the dialect_updater.py module."""


from typing import Generator

import pytest
from schema import SchemaError

from lexupdater import dialect_updater
from lexupdater.rule_objects import Rule


@pytest.fixture
def rule():
    """A test example of a structured rule from a ruleset."""
    return Rule.from_dict({
        "pattern": r"\bAX0 R$",
        "replacement": r"AA0 R",
        "constraints": [
            {"field": "pos", "pattern": "NN", "is_regex": False},
            {"field": "feats", "pattern": "MAS", "is_regex": True},
        ],
    })


def test_parse_constraints(rule):
    # given
    constraints = rule.constraints
    # when
    result_list, result_values = dialect_updater.parse_constraints(
        constraints
    )
    # then
    assert result_values == ("NN", "MAS")
    assert "pos = ?" in result_list
    assert "feats REGEXP ?" in result_list


def test_parse_constraints_with_empty_input():
    result_strings, result_values = dialect_updater.parse_constraints([])
    # then
    assert result_values == []
    assert result_strings == []


@pytest.mark.parametrize(
    "words, expected",
    [
        (["garn", "klarne"], "w.wordform NOT IN (?, ?)"),
        (["1", "2", "3"], "w.wordform NOT IN (?, ?, ?)"),
        ([], "")
    ]
)
def test_parse_exemptions(words, expected):
    # when
    result_string = dialect_updater.parse_exemptions(words)
    # then
    assert result_string == expected


def test_parse_conditions(rule):
    # given
    input_exemptions = ["biler", "båter"]
    expected = (
        'pos = ? AND feats REGEXP ? AND w.wordform NOT IN (?, ?)',
        ['NN', 'MAS', 'biler', 'båter']
    )
    # when
    result = dialect_updater.parse_conditions(rule.constraints, input_exemptions)
    # then
    assert result == expected, result


def test_parse_conditions_without_conditions():
    # given
    input_constraints = []
    input_exemptions = []
    # when
    result = dialect_updater.parse_conditions(input_constraints, input_exemptions)
    # then
    assert result == ("", [])


def test_parse_rulesets(ruleset_dict_list, exemptions_dict):
    # given
    expected_first_item = {'pattern': '\\b(R)([NTD])\\b', 'replacement': '\\1 \\2', 'constraints': []}

    # when
    result = dialect_updater.parse_rulesets(
        ruleset_dict_list, exemptions_dict
    )
    result_list = list(result)
    # then
    assert isinstance(result, Generator)
    assert result_list[0] == expected_first_item

@pytest.mark.skip("Not implemented")
def test_parse_rulesets_invalid_rules(ruleset_dict_list, exemptions_dict):
    """Test validation of rules."""
    # given
    rulesets = ruleset_dict_list + [{"unexpected_key": "unexpected_value"}]
    # when
    with pytest.raises(SchemaError):
        dialect_updater.parse_rulesets(
            rulesets, exemptions_dict
        )

@pytest.mark.skip("Not implemented")
def test_parse_rulesets_invalid_exemptions(ruleset_dict_list, exemptions_dict):
    """Test validation of exemptions."""
    # given
    exemptions_dict["unexpected_key"] = "unexpected_value"
    # when
    with pytest.raises(SchemaError):
        dialect_updater.parse_rulesets(
            ruleset_dict_list, exemptions_dict
        )
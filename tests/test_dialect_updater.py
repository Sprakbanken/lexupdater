"""Test suite for all the classes in the dialect_updater.py module."""

from typing import Generator

import pytest
from schema import SchemaError

from lexupdater import dialect_updater


@pytest.fixture
def rule():
    """A test example of a structured rule from a ruleset."""
    return {
        "pattern": r"\bAX0 R$",
        "replacement": r"AA0 R",
        "constraints": [
            {"field": "pos", "pattern": "NN", "is_regex": False},
            {"field": "feats", "pattern": "MAS", "is_regex": True},
        ],
    }


def test_parse_constraints(rule):
    # given
    constraints = rule["constraints"]
    # when
    result_list, result_values = dialect_updater.parse_constraints(
        constraints
    )
    # then
    assert result_values == ["NN", "MAS"]
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


def test_map_rule_exemptions():
    # given
    input_exemptions = [{"ruleset": "test", "words": ["garn", "klarne"]}]
    expected = {"test": ["garn", "klarne"]}
    # when
    result = dialect_updater.map_rule_exemptions(input_exemptions)
    # then
    assert list(result.keys()) == list(expected.keys())
    assert list(result.values()) == list(expected.values())


def test_parse_conditions(rule):
    # given
    input_exemptions = ["biler", "båter"]
    expected = (
        ["pos = ?", "feats REGEXP ?", "w.wordform NOT IN (?, ?)"],
        ['NN', 'MAS', 'biler', 'båter']
    )
    # when
    result = dialect_updater.parse_conditions(rule["constraints"], input_exemptions)
    # then
    assert result == expected


def test_parse_conditions_without_conditions():
    # given
    input_constraints = []
    input_exemptions = []
    # when
    result = dialect_updater.parse_conditions(input_constraints, input_exemptions)
    # then
    assert result == ("", [])


def test_parse_rules(some_dialects, ruleset_dict_list, exemptions_list):
    # given
    expected_first_item = (
        "e_spoken",
        r"\b(R)([NTD])\b",
        r"\1 \2",
        ["w.wordform NOT IN (?, ?)"],
        ["garn", "klarne"]
    )
    # when
    result = dialect_updater.parse_rules(
        some_dialects, ruleset_dict_list, exemptions_list
    )
    # then
    assert isinstance(result, Generator)
    assert list(result)[0] == expected_first_item


@pytest.mark.parametrize(
    "invalid_config_values",
    ["rules", "exemptions"],
    indirect=True
)
def test_parse_rules_invalid_input(some_dialects, invalid_config_values):
    """Test validation of rules and exemptions."""
    # given
    rulesets, exemptions = invalid_config_values
    # when
    result = dialect_updater.parse_rules(
        some_dialects, rulesets, exemptions
    )
    # then
    assert all([values for values in result])

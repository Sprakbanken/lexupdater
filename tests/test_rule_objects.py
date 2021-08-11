"""Test suite for Rule and RuleSet classes and helper functions."""
import re

import pytest
from schema import SchemaError

from lexupdater.constants import ruleset_schema, rule_schema
from lexupdater import rule_objects


@pytest.fixture
def proper_constraints():
    """List with a real-valued constraint dictionary."""
    return [{"field": "pos", "pattern": r"NN", "is_regex": False}]


def test_create_constraint_dict():
    # given
    expected = {
        "field": "test_field",
        "pattern": "test_pattern",
        "is_regex": False
    }
    # when
    result = rule_objects.create_constraint_dict(
        field="test_field",
        pattern="test_pattern",
        is_regex=False)
    # then
    assert str(result) == str(expected)


@pytest.mark.parametrize(
    "filename", ("tests/dummy_rules.py", "non_existent_rules.py"))
def test_verify_all_rulesets(filename, ruleset_fixture):
    # when
    result = rule_objects.verify_all_rulesets(filename, [ruleset_fixture])
    # then
    assert result is None


def test_verify_all_rulesets_raises_error(ruleset_fixture):
    filename = "tests/dummy_rules.py"
    with pytest.raises(ValueError):
        rule_objects.verify_all_rulesets(filename, 2 * [ruleset_fixture])


@pytest.mark.parametrize("dupes,reps", [(["test_rule_set"], 2), ([], 1)])
def test_check_duplicate_ruleset_names(dupes, reps, ruleset_fixture):
    # when
    result = rule_objects.check_duplicate_ruleset_names([ruleset_fixture]*reps)
    assert dupes == result
    assert len(dupes) == len(result)


def test_save_rules_and_exemptions(ruleset_fixture, tmp_path):
    # given
    r_file = (tmp_path / "rules.py")
    e_file = (tmp_path / "exemptions.py")
    expected_rules = "\ntest_rule_set = (.*)\n"
    expected_exemptions = "\nexemption_(.+) = (.*)\n"
    # when
    rule_objects.save_rules_and_exemptions([ruleset_fixture], tmp_path)
    # then
    assert r_file.exists()
    assert r_file.is_file()
    match_result_rules = re.match(expected_rules, r_file.read_text())
    assert match_result_rules is not None
    # and
    assert e_file.exists()
    assert e_file.is_file()
    match_result_exemptions = re.match(expected_exemptions, e_file.read_text())
    assert match_result_exemptions is not None


class TestRule:

    def test_rule_constructor(self, rule_fixture):
        # when
        result = rule_objects.Rule(
            pattern="transcription_pattern_to_replace",
            replacement="new_transcription"
        )
        assert isinstance(result, rule_objects.Rule)
        assert result.pattern == "transcription_pattern_to_replace"
        assert result.replacement == "new_transcription"
        assert result.constraints == []
        assert result.is_valid
        # id_ is a hash of pattern and replacement
        assert result.id_ == rule_fixture.id_
        # equality check also includes constraints
        assert result != rule_fixture

    def test_rule_constructor_invalid_rule(self):
        with pytest.raises(SchemaError):
            result = rule_objects.Rule(pattern=1, replacement=2, constraints=[3])
            assert isinstance(result, rule_objects.Rule)
            assert not result.is_valid

    @pytest.mark.parametrize(
        "new_constraints",
        ([{"field": "f", "pattern": "p", "is_regex": True}],[])
    )
    def test_constraints(self, new_constraints, rule_fixture):
        # given
        initial = rule_fixture.constraints.copy()
        # when
        rule_fixture.constraints = new_constraints
        # then
        assert rule_fixture.constraints != initial
        assert rule_fixture.constraints == new_constraints

    @pytest.mark.parametrize(
        "new_constraints",
        ({"field": 0, "pattern": 0, "is_regex": 0},
         ["not", "dicts", {}],
         [{"invalid": "dict"}],
         "string"),
        ids=["dict", "invalid_list", "invalid_list2", "str"])
    def test_invalid_constraints(self, rule_fixture, new_constraints):
        # given
        initial = rule_fixture.constraints.copy()
        # when
        rule_fixture.constraints = new_constraints
        # then
        assert initial == rule_fixture.constraints


    def test_add_constraint(self, rule_fixture, proper_constraints):
        # given
        initial = rule_fixture.constraints.copy()
        valid_dict = {
            "field": "column_name", "pattern": "value", "is_regex": True
        }
        proper = proper_constraints[0]
        # when
        rule_fixture.add_constraint(valid_dict)  # add full dict

        rule_fixture.add_constraint(  # add with parameters
            field=proper["field"],
            pattern=proper["pattern"],
            is_regex=proper["is_regex"]
        )
        # then
        assert valid_dict in rule_fixture.constraints
        assert proper in rule_fixture.constraints
        # adding new constraints shouldn't overwrite the original ones
        assert all(c in rule_fixture.constraints for c in initial)

    def test_from_dict(self):
        # given
        rule_dict = {
            "pattern": r"\b(R)([NTD])\b",
            "replacement": r"\1 \2",
            "constraints": []}
        # when
        result = rule_objects.Rule.from_dict(rule_dict)
        # then
        assert isinstance(result, rule_objects.Rule)
        assert result.is_valid
        assert result.pattern == r"\b(R)([NTD])\b"
        assert result.replacement == r"\1 \2"
        assert result.constraints == []

    def test_to_dict(self, rule_fixture):
        # when
        result = rule_fixture.to_dict()
        # then
        assert isinstance(result, dict)
        assert len(result.keys()) == 3
        assert "pattern" in result.keys()
        assert "replacement" in result.keys()
        assert "constraints" in result.keys()
        assert rule_schema.is_valid(result)

    def test_id_(self, rule_fixture, proper_constraints):
        # given
        original_id = rule_fixture.id_
        # when
        rule_fixture.constraints += proper_constraints
        same_id = rule_fixture.id_
        rule_fixture.pattern = "some_new_pattern"
        rule_fixture.replacement = "another_replacement"
        new_id = rule_fixture.id_
        # then
        assert original_id == same_id
        assert original_id != new_id

    def test_is_valid(self, rule_fixture):
        assert rule_fixture.is_valid
        # when
        rule_fixture.pattern = 10
        rule_fixture.replacement = 500
        # then
        assert not rule_fixture.is_valid

    def test_constraints(self, rule_fixture, proper_constraints):
        # given
        original_constraints = rule_fixture.constraints.copy()
        # when
        rule_fixture.constraints = ["some", "invalid","constraints", "here"]
        same_constraints = rule_fixture.constraints.copy()
        rule_fixture.constraints = proper_constraints
        new_constraints = rule_fixture.constraints.copy()
        # then
        assert original_constraints == same_constraints
        assert original_constraints != new_constraints


class TestRuleSet:

    def test_from_dict(self):
        # given
        test1 = {
            "areas": ["e_spoken", "vestnorsk"],
            "name": "retrotest",
            "rules": [
                {"pattern": r"\b(R)([NTD])\b", "replacement": r"\1 \2",
                 "constraints": []},
                {"pattern": r"\b(R)(NX0)\b", "replacement": r"\1 AX0 N",
                 "constraints": []},
            ],
        }
        # when
        result = rule_objects.RuleSet.from_dict(test1)
        # then
        assert isinstance(result,rule_objects.RuleSet)
        assert result.name == "retrotest"
        assert result.areas[0] == "e_spoken"
        assert len(result.areas) == 1
        assert len(result.rules) == 2
        assert isinstance(result.rules[0],rule_objects.Rule)
        assert result.rules[0].is_valid
        assert result.exempt_words == []

    def test_to_dict(self, ruleset_fixture):
        # when
        result = ruleset_fixture.to_dict()
        # then
        assert isinstance(result, dict)
        assert len(result.keys()) == 3
        assert "name" in result.keys()
        assert "areas" in result.keys()
        assert "rules" in result.keys()
        assert ruleset_schema.is_valid(result)

    def test_rules(self, ruleset_fixture):
        # given
        original_rules = ruleset_fixture.rules.copy()
        # when
        ruleset_fixture.rules = ["hello", "world"]
        # then
        assert ruleset_fixture.rules == original_rules

    def test_index_rules(self, rule_fixture, ruleset_fixture):
        # when
        result_idx = ruleset_fixture.index_rules(rule_obj=rule_fixture)
        result_rule = ruleset_fixture.index_rules(idx=0)
        result_index = ruleset_fixture.index_rules()
        # then
        assert isinstance(result_idx, int)
        assert result_idx == 0
        assert isinstance(result_rule, rule_objects.Rule)
        assert result_rule == rule_fixture
        assert isinstance(result_index, dict)
        assert str(result_index) == "{0: " + str(rule_fixture) + "}"

    def test_add_rule_no_dupes(self, ruleset_fixture):
        # given
        test_rule = rule_objects.Rule(pattern="test1", replacement="test2")
        # when
        ruleset_fixture.add_rule(test_rule)
        ruleset_fixture.add_rule(test_rule.to_dict())
        ruleset_fixture.add_rule(pattern=test_rule.pattern,
                                 replacement=test_rule.replacement)
        # then
        assert len(ruleset_fixture.rules) == 2  # rules are not duplicated

    def test_add_rule_obj(self, ruleset_fixture):
        # given
        test_rule = rule_objects.Rule(pattern="test1", replacement="test2")
        # when
        ruleset_fixture.add_rule(test_rule)
        # then
        assert test_rule in ruleset_fixture.rules

    def test_add_rule_dict(self, ruleset_fixture):
        # given
        test_rule = rule_objects.Rule(pattern="test1", replacement="test2")
        # when
        ruleset_fixture.add_rule(test_rule.to_dict())
        # then
        assert test_rule in ruleset_fixture.rules

    def test_add_rule_params(self, ruleset_fixture):
        # given
        test_rule = rule_objects.Rule(pattern="test1", replacement="test2")
        # when
        ruleset_fixture.add_rule(pattern=test_rule.pattern,
                                 replacement=test_rule.replacement)
        # then
        assert test_rule in ruleset_fixture.rules

    def test_add_multiple_rules(self, ruleset_fixture):
        # given
        test_rule1 = rule_objects.Rule(pattern="test1",
                                       replacement="replacement1")
        test_rule2 = rule_objects.Rule(pattern="test2",
                                       replacement="replacement2")
        invalid_rule = "invalid_rule_object"
        input_rules = [test_rule1,test_rule2, invalid_rule]
        # when
        ruleset_fixture.add_multiple_rules(input_rules)
        # then
        assert len(ruleset_fixture.rules) == 3
        assert all([rule.is_valid for rule in ruleset_fixture.rules])

    def test_create_exemption_dict(self, ruleset_fixture):
        # given
        expected = {"ruleset": "test_rule_set", "words": ["exempt_word"]}
        # when
        result = ruleset_fixture.create_exemption_dict()
        # then
        assert str(expected) == str(result)

"""Test suite for Rule and RuleSet classes and helper functions."""
import re

import pytest

from lexupdater.constants import ruleset_schema, rule_schema
from lexupdater import rule_objects


@pytest.mark.skip("Deprecated")
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
    """Test that the function handles nonexistent files and returns None when there are no duplicates."""
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

#@pytest.mark.skip(reason="one by one")
class TestRule:

    def test_rule_constructor(self):
        # when
        result = rule_objects.Rule(
            pattern="transcription_pattern_to_replace",
            replacement=r"D DH \1 EE1"
        )
        assert isinstance(result, rule_objects.Rule)
        assert result.pattern == "transcription_pattern_to_replace"
        assert result.replacement == r"D DH \1 EE1"
        assert result.constraints == []
        assert result.is_valid
        # hash_ is a hash of pattern and replacement
        assert result.id_ == result.hash_

    def test_rule_constructor_invalid_rule(self):
        #with pytest.raises(SchemaError):
        result = rule_objects.Rule(pattern=1, replacement=2, constraints=[3])
        assert isinstance(result, rule_objects.Rule)
        assert not result.is_valid

    @pytest.mark.parametrize(
        "new_constraints",
        ([{"field": "f", "pattern": "p", "is_regex": True}],[])
    )
    def test_constraints(self, new_constraints, proper_constraints):
        # given
        initial = proper_constraints.copy()
        ruleobject = rule_objects.Rule(pattern="test", replacement="test",constraints=initial)
        constraint_objs = [rule_objects.Constraint(**c) for c in initial]
        # when
        ruleobject.constraints = new_constraints
        # then
        assert ruleobject.constraints != initial
        assert ruleobject.constraints == constraint_objs


    @pytest.mark.parametrize(
        "new_constraints",
        ({"field": 0, "pattern": 0, "is_regex": 0},
         ["not", "dicts", {}],
         [{"invalid": "dict"}],
         "string"),
        ids=["dict", "invalid_list", "invalid_list2", "str"])
    def test_invalid_constraints(self, proper_constraints, new_constraints):
        # given
        initial = proper_constraints.copy()
        ruleobject = rule_objects.Rule(pattern="test", replacement="test",constraints=initial)
        constraint_objs = [rule_objects.Constraint(**c) for c in initial]
        # when
        ruleobject.constraints = new_constraints
        # then
        assert ruleobject.constraints == constraint_objs
        

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

    def test_rule_hash_(self, rule_fixture, proper_constraints):
        # given
        original_id = rule_fixture.hash_
        # when
        rule_fixture.constraints += proper_constraints
        same_id = rule_fixture.hash_
        rule_fixture.pattern = "some_new_pattern"
        rule_fixture.replacement = r"T EH0 S T \1"
        new_id = rule_fixture.hash_
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

    def test_index(self, rule_fixture, ruleset_fixture):
        # when
        result_index = ruleset_fixture.rules_index
        # then
        assert isinstance(result_index, dict)
        assert str(result_index) == "{0: " + str(rule_fixture) + "}"

    def test_get_rule(self, rule_fixture, ruleset_fixture):
        result_rule = ruleset_fixture.get_rule(rule_fixture.hash_)
        assert isinstance(result_rule, rule_objects.Rule)
        assert result_rule == rule_fixture

    def test_get_idx_number(self, rule_fixture, ruleset_fixture):
        result_idx = ruleset_fixture.get_idx_number(rule_fixture)
        assert isinstance(result_idx, int)
        assert result_idx == 0

    def test_add_rule_no_dupes(self, ruleset_fixture):
        # given
        test_rule = rule_objects.Rule(pattern="test1",
                                      replacement=r"T EH0 S T \2")
        test_rule_dict = test_rule.to_dict()
        # when
        ruleset_fixture.add_rule(test_rule)
        ruleset_fixture.add_rule(test_rule_dict)
        ruleset_fixture.add_rule(pattern=test_rule.pattern,
                                 replacement=test_rule.replacement)
        # then
        assert len(ruleset_fixture.rules) == 2  # rules are not duplicated

    def test_add_rule_obj(self, ruleset_fixture):
        # given
        test_rule = rule_objects.Rule(pattern="test1",
                                      replacement=r"T EH0 S T \2")
        # when
        ruleset_fixture.add_rule(test_rule)
        # then
        assert test_rule in ruleset_fixture.rules

    def test_add_rule_dict(self, ruleset_fixture):
        # given
        test_rule = rule_objects.Rule(pattern="test1",
                                      replacement=r"T EH0 S T \2")
        # when
        ruleset_fixture.add_rule(test_rule.to_dict())
        # then
        assert test_rule in ruleset_fixture.rules

    def test_add_rule_params(self, ruleset_fixture):
        # given
        test_rule = rule_objects.Rule(pattern="test1",
                                      replacement=r"T EH0 S T \2")
        # when
        ruleset_fixture.add_rule(pattern=test_rule.pattern,
                                 replacement=test_rule.replacement)
        # then
        assert test_rule in ruleset_fixture.rules

    def test_add_rules(self):
        # given
        test_rule1 = dict(
            pattern="test1",
            replacement=r"T EH0 S T \1")
        test_rule2 = dict(
            pattern="test2",
            replacement=r"T EH0 S T \2")


        ruleset = rule_objects.RuleSet(name="test_rule_set", areas=["e_spoken"])
        # when
        ruleset.rules += [test_rule1, test_rule2]
        # then
        assert len(ruleset.rules) == 2, ruleset.rules
        assert all([rule.is_valid for rule in ruleset.rules])


    def test_add_rule_invalid(self, ruleset_fixture):
        invalid_rule = "invalid_rule_object"
        with pytest.raises(ValueError):
            ruleset_fixture.add_rule(invalid_rule)

    def test_create_exemption_dict(self, ruleset_fixture):
        # given
        expected = {"ruleset": "test_rule_set", "words": ["exempt_word"]}
        # when
        result = ruleset_fixture.create_exemption_dict()
        # then
        assert str(expected) == str(result)


def test_map_rule_exemptions():
    # given
    input_exemptions = [{"ruleset": "test", "words": ["garn", "klarne"]}]
    expected = {"test": ["garn", "klarne"]}
    # when
    result = rule_objects.map_rule_exemptions(input_exemptions)
    # then
    assert list(result.keys()) == list(expected.keys())
    assert list(result.values()) == list(expected.values())


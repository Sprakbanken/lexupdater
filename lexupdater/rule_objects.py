import logging
from collections import Counter
from pathlib import Path
from typing import List, Union, Iterable

from schema import SchemaError

from .constants import (
    dialect_schema,
    rule_schema,
    constraint_schema,
    exemption_schema,
    ruleset_schema
)
from .utils import (
    filter_list_by_list,
    load_data,
    validate_objects,
    format_rulesets_and_exemptions,
    ensure_path_exists
)


def create_constraint_dict(
        field: str, pattern: str, is_regex: bool
) -> dict:
    """Create a well-formed constraint dictionary."""
    constraint = {
        "field": field,
        "pattern": pattern,
        "is_regex": is_regex
    }
    return constraint_schema.validate(constraint)


class Rule:
    """Replacement rule used to transform transcription entries in the lexicon.

    Each rule contains a regex pattern, a replacement string,
    and optionally a list of extra constraints.
    """
    def __init__(
            self, pattern: str, replacement: str, constraints: list = None
    ):
        self.pattern = pattern
        self.replacement = replacement
        self._constraints = [] if constraints is None else validate_objects(
            constraints,
            constraint_schema
        )
        if not self.is_valid:
            logging.error("Instatiated an invalid rule: %s", self)

    @classmethod
    def from_dict(cls, rule_dict: dict):
        """Instantiate a Rule object from a valid rule dictionary.

        Parameters
        ----------
        rule_dict: dict
            Format is {"pattern": str, "replacement": str, "constraints": list}
        """
        return cls(**rule_dict)

    def to_dict(self):
        """Create a well-formed replacement rule dict."""
        rule_dict = {
            'pattern': self.pattern,
            'replacement': self.replacement,
            'constraints': self.constraints
        }
        return rule_schema.validate(rule_dict)

    def __repr__(self):
        instance_repr = (
            "{}(pattern={!r}, replacement={!r}, constraints={!r})"
        ).format(
            self.__class__.__name__,
            self.pattern,
            self.replacement,
            self.constraints
        )
        return instance_repr

    def __str__(self):
        return str(self.to_dict())

    def __eq__(self, other):
        return hash(str(self)) == hash(str(other))

    @property
    def id_(self):
        """Identifier to differ between rules in the RuleSet.rules collection.

        This property is deliberately not implemented as the magic
        method __hash__, because the magic method would make Rule objects
        immutable, and obscure the fact that two almost "identical" rules can
        have different constraints.

        Source:
        https://docs.python.org/3/reference/datamodel.html#object.__hash__
        """
        return hash((self.pattern, self.replacement))

    @property
    def is_valid(self):
        """Whether or not the rule is valid."""
        try:
            dict_format = self.to_dict()
        except SchemaError:
            return False
        return rule_schema.is_valid(dict_format)

    @property
    def constraints(self):
        """Extra conditions for the rule to apply to a word's transcription.

        Each constraint specifies a field (e.g. "pos" or "feats"),
        a pattern (e.g. "NN" or "FEM") and a boolean value is_regex,
        which ensures the pattern matches the lexicon value
        either partially (True) or fully (False).
        """
        return self._constraints

    @constraints.setter
    def constraints(self, constraint_list):

        original_constraints = self._constraints.copy()
        if len(constraint_list) == 0:
            logging.debug("Resetting the constraints to an empty list.")
            self._constraints = []
        else:
            self._constraints = []
            for constraint in constraint_list:
                self.add_constraint(constraint)
            if len(self._constraints) == 0:
                logging.debug("No valid constraints were added from %s. "
                              "Keeping original list: %s",
                              constraint_list, original_constraints)
                self._constraints = original_constraints

    def add_constraint(
            self,
            constraint: dict = None,
            field: str = None,
            pattern: str = None,
            is_regex: bool = True
    ):
        """Append a valid constraint dict to self.constraints.

        Either provide a pre-defined dict
        (e.g. constructed and validated with create_constraint_dict()),
        or pass the field, pattern and is_regex arguments directly.
        """
        if (not constraint) and field and pattern:
            constraint = create_constraint_dict(
                field=field,
                pattern=pattern,
                is_regex=is_regex
            )
        if isinstance(constraint, dict) and \
                constraint_schema.is_valid(constraint):

            unique_constraints = {str(c) for c in self.constraints}
            if str(constraint) not in unique_constraints:
                self._constraints.append(constraint)
        else:
            logging.debug(
                "Skipping invalid constraint: %s \n"
                "The constraints must be dicts in this format: %s",
                constraint, constraint_schema.schema)


class RuleSet:
    """A named collection of replacement rules for specific dialects."""
    def __init__(
            self,
            name: str,
            areas: list = None,
            rules: list = None,
            exempt_words: list = None,
    ):
        self.name: str = name
        self._areas: List = filter_list_by_list(areas, dialect_schema.schema)
        self._rules: List = []
        self._exempt_words: List = [] if exempt_words is None else exempt_words

        if rules is not None:
            self.add_multiple_rules(rules)

    @classmethod
    def from_dict(cls, ruleset_dict: dict):
        """Instantiate a RuleSet object from a valid ruleset dictionary.

        Parameters
        ----------
        ruleset_dict: dict
            Format is {"name": str, "areas": list, "rules": list}
        """
        instance = cls(**ruleset_dict, exempt_words=None)
        return instance

    def to_dict(self):
        """Create a rule set dict with validated rule dicts."""
        ruleset = {
            "name": self.name,
            "areas": self.areas,
            "rules": [rule.to_dict() for rule in self.rules],
        }
        return ruleset_schema.validate(ruleset)

    def __repr__(self):
        """String representation of the RuleSet instance."""
        instance_repr = (
            "{}(name={!r}, areas={!r}, rules={!r}, exempt_words={!r})"
        ).format(
            self.__class__.__name__,
            self.name, self.areas, self.rules, self.exempt_words
        )
        return instance_repr

    def __str__(self):
        return str(self.to_dict())

    def __eq__(self, other):
        return hash(str(self)) == hash(str(other))

    @property
    def areas(self):
        """Dialects that the set of rules apply to."""
        return self._areas

    @areas.setter
    def areas(self, areas: list):
        self._areas = filter_list_by_list(areas, dialect_schema.schema)
        self._areas = list(set(self._areas))

    @property
    def rules(self):
        """Collection of replacement rules.

        Rules have a regex pattern, string replacement,
        and optionally a list of constraints.
        """
        return self._rules

    @rules.setter
    def rules(self, rule_list: list):
        original_rules = self._rules.copy()
        if len(rule_list) == 0:
            logging.debug("Resetting the rules to an empty list.")
            self._rules = []
        else:
            self._rules = []
            self.add_multiple_rules(rule_list)
            if len(self._rules) == 0:
                logging.debug("No valid rules were added from the list: %s. "
                              "Keeping original values: %s",
                              rule_list, original_rules)
                self._rules = original_rules

    @property
    def exempt_words(self):
        """Words to be ignored for the rules in the ruleset."""
        return self._exempt_words

    @exempt_words.setter
    def exempt_words(self, new_exemptions):
        self._exempt_words = list(set(new_exemptions))

    def view_rules_index(self, rule_obj: Rule = None, idx: int = None):
        """Regular and reverse lookup of rules in the ruleset.

        If rule_obj is provided, return the corresponding index
        number of the rule in the rules attribute

        If idx is provided, return the corresponding rule from the rules
        attribute.

        If no args: Return a dictionary with enumerated rules as dicts.
        Format
        {index_number: {"pattern":str, "replacement": str, "constraints": list}
        """
        idx_to_id = {i: rule.id_ for i, rule in enumerate(self._rules)}
        id_to_index = {id_: i for i, id_ in idx_to_id.items()}
        idx_to_dict = {i: rule.to_dict() for i, rule in enumerate(self._rules)}

        if rule_obj is not None and rule_obj.id_ in id_to_index:
            return id_to_index[rule_obj.id_]
        if idx is not None and idx in idx_to_id:
            return self._rules[idx]
        return idx_to_dict

    def add_rule(self,
                 rule=None,
                 pattern: str = None,
                 replacement: str = None,
                 constraints: list = None):
        """Wrapper to create a Rule object and add it to self.rules.

        Either pass a valid dict, a Rule instance,
        or provide each of the fields pattern, replacement and constraints
        explicitly.

        Parameters
        ----------
        rule: Rule or dict
            A valid instance of the Rule class,
            or a dict with "pattern", "repl" and "constraints" keys
        pattern: str
        replacement: str
        constraints: list
            Collection of constraint dicts.
            See the create_constraint_dict() function.
        """
        args = vars()
        if rule is None and (pattern and replacement):
            rule = Rule(
                pattern=pattern,
                replacement=replacement,
                constraints=constraints
            )
        elif isinstance(rule, dict) and rule_schema.is_valid(rule):
            rule = Rule.from_dict(rule)
        elif not isinstance(rule, Rule):
            raise ValueError(f"Invalid rule arguments: {args}")
        assert rule is not None
        assert rule.is_valid, f"Invalid rule: {rule}"
        if rule not in self.rules:
            self._rules.append(rule)
            logging.debug("Adding %s to self.rules", rule)
        else:
            index_number = self.view_rules_index(rule_obj=rule)
            logging.debug(
                "Skipping: Rule with pattern=%s and replacement=%s already "
                "exists: self.rules[%s]", rule.pattern, rule.replacement,
                index_number)

    def add_multiple_rules(self, rule_list):
        """Add a collection of rules to self.rules."""
        for rule_obj in rule_list:
            try:
                self.add_rule(rule_obj)
            except (AssertionError, ValueError) as error:
                logging.debug(
                    "Skipping invalid rule: %s due to %s. "
                    "The rule_list must contain either Rule objects "
                    "or dicts in this format: %s",
                    rule_obj, error, rule_schema.schema)

    def create_exemption_dict(self) -> dict:
        """Create an exemption dictionary with self.exempt_words."""
        exemption = {
            "ruleset": self.name,
            "words": self.exempt_words,
        }
        return exemption_schema.validate(exemption)


def verify_all_rulesets(rule_file: Union[str, Path], ruleset_list: list):
    """Verify that no new or existing rule sets share the same name."""
    try:
        file_rules = load_data(rule_file)
        file_rulesets = [RuleSet.from_dict(r_dict) for r_dict in file_rules]
        all_rulesets = file_rulesets + list(ruleset_list)
    except AssertionError:
        all_rulesets = list(ruleset_list)
    duplicates = check_duplicate_ruleset_names(all_rulesets)
    if duplicates:
        raise ValueError(f"Ruleset names are not unique: {duplicates}")


def check_duplicate_ruleset_names(rulesets: Iterable):
    """Check if any rule sets share the same name."""
    seen = Counter([ruleset.name for ruleset in rulesets])
    duplicates = [name for name in seen if seen[name] >= 2]
    if duplicates:
        print("Some rulesets have the same names: ", duplicates)
        print("Change their names before saving them to file.")
    return duplicates


def save_rules_and_exemptions(
        ruleset_list: list, output_dir: Union[str, Path] = "."):
    """Format rule sets and exemptions, and save to their designated files."""
    out_dir = ensure_path_exists(output_dir)
    rule_file = out_dir / "rules.py"
    exemptions_file = out_dir / "exemptions.py"
    verify_all_rulesets(rule_file, ruleset_list)
    rules, exemptions = format_rulesets_and_exemptions(ruleset_list)
    with rule_file.open(mode="a+", encoding="utf-8") as r_file:
        r_file.write(rules)
    with exemptions_file.open(mode="a+", encoding="utf-8") as e_file:
        e_file.write(exemptions)

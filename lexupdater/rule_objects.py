import logging
from collections import Counter
from pathlib import Path
from typing import List, Union, Iterable, Generator

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
    return constraint

class Constraint:
    def __init__(self, constraint_dict) -> None:

        self.field = constraint_dict.get("field")
        self.pattern = constraint_dict.get("pattern")
        self.is_regex = constraint_dict.get("is_regex")

    def __str__(self) -> str:
        return str(self.to_dict())

    def __hash__(self):
        return hash((self.field, self.pattern, self.is_regex, self.is_valid))

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self.to_dict())})"

    def is_valid(self):
        return constraint_schema.is_valid(self.to_dict())

    def to_dict(self):
        return create_constraint_dict(self.field, self.pattern, self.is_regex)



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
        self.id_ = self.hash_
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
    def hash_(self):
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
        """Conditions for the rule to apply to a word's transcription.

        Each constraint specifies a field (e.g. "pos" or "feats"),
        a pattern (e.g. "NN" or "FEM") and a boolean value is_regex,
        which ensures the pattern matches the lexicon value
        either partially (True) or fully (False).
        """
        return self._constraints

    @constraints.setter
    def constraints(self, constraint_list):
        constraints = [Constraint(const) for const in constraint_list]
        assert all(const.is_valid for const in constraints)
        self._constraints = constraints


class RuleObj(Rule):

    def __init__(
        self,
        pattern: str = None,
        replacement: str = None,
        constraints: list = None,
        ruleset: str = None,
        dialect: str = None,
        exemptions: list = None,
        idx: int = 0,
    ):
        super().__init__(pattern, replacement, constraints)
        self.ruleset = ruleset
        self.dialect = dialect
        self.exemptions = [] if exemptions is None else exemptions
        self.id_ = f"{self.ruleset}_{self.dialect}_{idx}"


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
    def from_dict(cls, ruleset_dict: dict, exemptions: list = None):
        """Instantiate a RuleSet object from a valid ruleset dictionary.

        Parameters
        ----------
        ruleset_dict: dict
            Format is {"name": str, "areas": list, "rules": list}
        exemptions: list
            Words that are exempt from the rules in the ruleset.
        """
        instance = cls(**ruleset_dict, exempt_words=exemptions)
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

    @property
    def idx_to_id(self):
        """Mapping of rules index to the rule.hash_ number."""
        return {i: rule.hash_ for i, rule in enumerate(self._rules)}

    @property
    def id_to_idx(self):
        """Reverse mapping of rule.hash_ numbers to the rules index."""
        return {id_: i for i, id_ in self.idx_to_id.items()}

    def get_idx_number(self, rule: Union[Rule, int]) -> int:
        """Reverse index lookup of a ``Rule`` object.

        Parameters
        ----------
        rule: Rule or int
            Either, provide a ``Rule`` object directly, or the ``Rule.hash_`` integer attribute

        Returns
        -------
        int: The corresponding index number of the rule in the `self.rules` list.
        """
        if isinstance(rule, Rule):
            return self.id_to_idx.get(rule.hash_)
        if isinstance(rule, int):
            return self.id_to_idx.get(rule)

    def get_rule(self, rule_id: int):
        """Lookup a ``Rule`` object given a Rule.hash_ number."""
        return self._rules[self.get_idx_number(rule_id)]

    @property
    def rules_index(self) -> dict:
        """Turn the indexed list of rules into a dictionary."""
        idx_to_dict = {i: rule.to_dict() for i, rule in enumerate(self._rules)}
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
            rule.id_ = f"{self.name}_{self.get_idx_number(rule)}"
        else:
            logging.debug(
                "Skipping: Rule with pattern=%s and replacement=%s already "
                "exists: %s (<ruleset[name]>_<ruleset.rules[index_number]>)",
                rule.pattern,
                rule.replacement,
                f"{self.name}_{self.get_idx_number(rule)}")

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


def construct_rulesets(
    rulesets: Iterable,
    exemptions: list,
) -> Generator:
    """Create RuleSet objects from a list of ruleset dicts and their corresponding exemptions.

    Returns
    -------
    Generator[tuple]: (ruleset name, RuleSet object)
        The RuleSet object's attribute exempt_words is also populated.
    """
    rule_exemptions = map_rule_exemptions(
        validate_objects(exemptions, exemption_schema)
    )
    for ruleset in rulesets:
        name = ruleset.get("name")
        try:
            ruleset = RuleSet.from_dict(
                ruleset, exemptions=rule_exemptions.get(name)
            )
        except TypeError:
            logging.error("Already a RuleSet: %s", name)
        yield ruleset


def filter_rulesets_by_dialects(rulesets: Iterable, dialects: Iterable) -> Generator:
    """Filter the rulesets (and their 'areas' attribute) by the given dialects."""
    for ruleset in rulesets:
        ruleset.areas = filter_list_by_list(ruleset.areas, dialects)
        if ruleset.areas:
            yield ruleset


def fetch_ruleset_dialects(rulesets: Iterable) -> list:
    return list({d for ruleset in rulesets for d in ruleset.areas})


def index_rulesets(rulesets: Generator) -> tuple:
    """Create an index of the rulesets where the name is the key and the value is the index
    number in the original list."""
    index_dict = {}
    original_list = []
    for idx, ruleset in enumerate(rulesets):
        original_list.append(ruleset)
        index_dict[ruleset.name] = idx
        for rule in ruleset.rules:
            index_dict[rule.id_] = idx
    return index_dict, original_list


def filter_rulesets_by_id(rulesets: Generator, rule_ids: list) -> list:
    ruleset_index, rulesets = index_rulesets(rulesets)
    last_relevant_rule = 0
    dialects = []
    for rule_id in rule_ids:
        idx = ruleset_index[rule_id]
        if idx > last_relevant_rule:
            last_relevant_rule = idx
        dialects += rulesets[idx].areas
    rulesets = list(filter_rulesets_by_dialects(rulesets, dialects))
    return rulesets[:last_relevant_rule+1]  # Include the last rule in the slice


def preprocess_rules(
        rules_file, exemptions_file, rule_ids: list = None, config_dialects: list = None) -> tuple:
    """Load and filter rules and exemptions.

    Filter rules on the selected ids, if any, and filter dialects on the relevant rules.
    """
    rules = load_data(rules_file)
    exemptions = load_data(exemptions_file) if exemptions_file is not None else []
    # Load the ruleset dicts from rules.py into RuleSet objects
    rulesets = list(construct_rulesets(rules, exemptions))
    if rule_ids is not None:
        rulesets = filter_rulesets_by_id(rulesets, rule_ids)
    if config_dialects is not None:
        rulesets = list(filter_rulesets_by_dialects(rulesets, config_dialects))
    relevant_dialects = fetch_ruleset_dialects(rulesets)
    return rulesets, relevant_dialects


def map_rule_exemptions(exemptions: List[str]) -> dict:
    """Reduce the list of exemption dictionaries to a single dictionary.

    The keys are the name of the corresponding ruleset,
    and the exempt words are the values.

    Parameters
    ----------
    exemptions: list
        list of dicts of the form ``{'ruleset': str, 'words': list}``
    """
    return {
        exemption["ruleset"]: exemption["words"]
        for exemption in exemptions
    }


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

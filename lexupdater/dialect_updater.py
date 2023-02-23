"""Parse dialect-specific transformation rules.

Parse their constraints and exemptions
into variables to fill slots in SQL query templates.
"""

import logging
from typing import List, Generator

from .constants import ruleset_schema, COL_WORDFORM, rule_schema
from .utils import filter_list_by_list, load_exemptions, load_rules, validate_objects, add_placeholders
from .rule_objects import RuleObj


def sql_operator(is_regex):
    return "REGEXP" if is_regex else "="


def parse_constraint(constraint) -> tuple:
    """Define SQL statement fragment to follow 'WHERE' """
    return f"{constraint.field} {sql_operator(constraint.is_regex)} ?", constraint.pattern


def parse_constraints(constraints: List) -> List[tuple]:
    """Construct SQL WHERE queries from the replacement rule constraints.

    Grammatical categories and features that are given in the word table of
    the lexicon can be used to narrow down the scope of words that the
    replacement rule applies to.

    Parameters
    ----------
    constraints: list[dict]
        list of dictionaries with `field`, `pattern`, and `is_regex` keys

    Returns
    -------
    tuple[str, list]
        SQL clause fragment and list of feature values
        for the words that the rule applies to
    """
    return [parse_constraint(c) for c in constraints]


def parse_exemptions(exemption_words):
    """Parse an exemption dictionary and convert to a WHERE clause fragment.

    Parameters
    ----------
    exemption_words: list
        list of words to exclude from the word search

    Returns
    -------
    tuple[str, list]
        SQL fragment and a list of words that are exempt
    """
    if exemption_words:
        return f"{COL_WORDFORM} NOT IN ({add_placeholders(exemption_words)})", exemption_words
    return ""


def parse_conditions(constraints: list, exempt_words: list, prefix: str = '') -> tuple:
    """Create an SQL WHERE-query fragment based on constraints and exemptions.

    The conditional fragment is meant to be inserted in
    a SELECT or UPDATE query, along with the values
    that fill the placeholder slots.
    """
    if not bool(constraints) and not exempt_words:
        return "", []

    constraints, cond_vals = parse_constraints(constraints)
    exemption, exempt_words = parse_exemptions(exempt_words)
    coordinated_conditions = coordinate_constraints(constraints+exemption, prefix=prefix)
    return coordinated_conditions, cond_vals + exempt_words


def coordinate_constraints(constraints, prefix: str = ''):
    coordinated_str = ' AND '.join(c for c in constraints if c)
    if prefix and coordinated_str:
        return f" {prefix} {coordinated_str}"
    return coordinated_str


def parse_rulesets(rulesets: list, exemptions: dict) -> Generator:
    """Parse a list of ruleset dicts and exemptions, yield rule objects with attributes for constructing SQL queries.

    Yields
    ------
    RuleObj
    """
    for ruleset in rulesets:
        name = ruleset.get("name")
        for dialect in ruleset.get("areas"):
            for idx, rule in enumerate(ruleset.get("rules")):
                ruleobject = RuleObj(**rule, ruleset=name, dialect=dialect,exemptions=exemptions.get(name), idx=idx)
                yield ruleobject


def preprocess_rulefiles(rulefile, exemptionfile):
    """Load files and parse the contents. Return a rule generator."""
    rulesets = load_rules(rulefile)
    exemptions = load_exemptions(exemptionfile)
    rules = parse_rulesets(rulesets, exemptions)
    return rules

"""Parse dialect-specific transformation rules.

Parse their constraints and exemptions
into variables to fill slots in SQL query templates.
"""
import functools
import logging
from typing import List, Generator

from .constants import ruleset_schema, exemption_schema, COL_WORDFORM
from .utils import filter_list_by_list, validate_objects, add_placeholders
from .rule_objects import map_rule_exemptions


def parse_constraints(constraints: List):
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
    values = []
    constraint_fragments = []
    for const in constraints:
        operator = "=" if not const["is_regex"] else "REGEXP"
        constraint_fragments.append(f"{const['field']} {operator} ?")
        values.append(const["pattern"])
    return constraint_fragments, values


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
        return f"{COL_WORDFORM} NOT IN ({add_placeholders(exemption_words)})"
    return ""


def parse_conditions(constraints: list, exempt_words: list) -> tuple:
    """Create an SQL WHERE-query fragment based on constraints and exemptions.

    The conditional fragment is meant to be inserted in
    a SELECT or UPDATE query, along with the values
    that fill the placeholder slots.
    """
    is_constrained = bool(constraints)
    if not is_constrained and not exempt_words:
        return "", []

    constraint_strs, constraint_values = parse_constraints(constraints)
    exempt_str = parse_exemptions(exempt_words)

    conditions = [string for string in (*constraint_strs, exempt_str) if string]
    values = constraint_values + exempt_words
    logging.debug("Conditions: %s ", conditions)
    logging.debug("Values: %s", values)
    return conditions, values


def parse_rules(
    filter_dialects: list,
    rulesets: list,
    exemptions: list,
) -> Generator:
    """Parse rulesets, and yield the values needed to construct SQL queries.

    Yields
    ------
    tuple
        str: dialect affected by the rule,
        str: regex pattern,
        str: replacement string,
        str: conditional query fragment,
        list: conditional values to fill placeholders
    """
    rule_exemptions = map_rule_exemptions(
        validate_objects(exemptions, exemption_schema)
    )
    validated_rules = validate_objects(rulesets, ruleset_schema)

    for ruleset in validated_rules:
        rule_dialects = filter_list_by_list(ruleset["areas"], filter_dialects)
        if not rule_dialects:
            continue
        logging.debug(
            "Parsing rule set '%s' for dialects %s",
            ruleset.get("name"),
            ", ".join(rule_dialects)
        )
        exempt_words = rule_exemptions.get(ruleset["name"], [])

        for rule in ruleset["rules"]:
            logging.debug("Rule pattern: %s", rule["pattern"])
            logging.debug("Rule replacement: %s", rule["replacement"])
            cond_string, cond_values = parse_conditions(
                rule["constraints"], exempt_words
            )
            for dialect in rule_dialects:
                print(".", end="")
                yield (
                    dialect,
                    rule["pattern"],
                    rule["replacement"],
                    cond_string,
                    cond_values
                )
    print("")

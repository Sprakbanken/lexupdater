#!/usr/bin/env python
# coding=utf-8
from typing import List


def parse_constraints(constraints: List):
    """Extract constraint values from replacement rules
    and construct SQL WHERE queries based on them.

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

    constraint_string = " AND ".join(constraint_fragments)
    return constraint_string, values


def parse_exemptions(exemption_words):
    """Parse an exemption dictionary and convert to a WHERE clause fragment

    Parameters
    ----------
    exemption_words: list
        list of words to exclude from the word search

    Returns
    -------
    tuple[str, list]
        SQL fragment and a list of words that are exempt
    """
    exemption_string = (
        f"wordform NOT IN ({','.join(['?' for _ in exemption_words])})"
    ) if exemption_words != [] else ""
    return exemption_string


def map_rule_exemptions(exemptions):
    """Reduce the list of exemption dictionaries to a single dictionary,
    where the name of the corresponding ruleset is the key, and the exempt
    words are the value.

    Parameters
    ----------
    exemptions: list
        list of strings, which should correspond

    Returns
    -------
    dict
    """
    return {
        exemption["ruleset"]: exemption["words"]
        for exemption in exemptions
    }


def construct_select_queries(rule, exemptions, dialects):
    """Not yet implemented.
    Build a select query that retrieves all entries
    that fits the search pattern, making it easier to test and debug.
    """
    pass

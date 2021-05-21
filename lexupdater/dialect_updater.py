#!/usr/bin/env python
# coding=utf-8

"""
Parse dialect-specific transformation rules, their constraints and exemptions
into variables to fill slots in SQL query templates.
"""

from typing import List


class QueryBuilder(object):
    """Parent class for querybuilder classes."""

    def __init__(self, area, rule, word_table):
        self._area = area
        self._word_table = word_table
        self._pattern = rule["pattern"]
        self._repl = rule["repl"]
        self._constraints = rule["constraints"]
        self._constrained_query = self._constraints != []


class UpdateQueryBuilder(QueryBuilder):
    """Build an sql update query string """

    def __init__(self, area, rule, word_table):
        QueryBuilder.__init__(self, area, rule, word_table)
        self._query = f"UPDATE {area} SET nofabet = REGREPLACE(?,?,nofabet)"
        self._values = [self._pattern, self._repl]
        if self._constrained_query:
            cstr, cvals = parse_constraints(
                self._constraints, self._word_table
            )
            self._query += cstr
            self._values = self._values + cvals

    def get_update_query(self):
        return self._query, self._values, self._constrained_query


class SelectQueryBuilder(QueryBuilder):
    """Not yet implemented. The idea is that
    it should build a select query that retrieves all entries
    that fits the search pattern, making it easier to test and debug.
    """

    pass


def parse_constraints(constraints: List, word_table: str):
    """Extract constraint values from replacement rules
    and construct SQL WHERE queries based on them.

    Grammatical categories and features that are given in the word table of
    the lexicon can be used to narrow down the scope of words that the
    replacement rule applies to.

    Parameters
    ----------
    constraints: list[dict]
        list of dictionaries with `field`, `pattern`, and `is_regex` keys
    word_table: str

    Returns
    -------
    tuple[str, list]
        SQL clause fragment and list of feature values
        for the words that the rule applies to
    """
    values = []
    constraint_string = (
            f" WHERE word_id IN (SELECT word_id FROM {word_table} WHERE "
        )
    for n, const in enumerate(constraints):
        pattern = const["pattern"]
        values.append(pattern)

        field = const["field"]
        operator = "=" if not const["is_regex"] else "REGEXP"
        constraint_string += f"{field} {operator} ?"

        if n != len(constraints) - 1:
            constraint_string += " AND "

    return constraint_string, values


def parse_exemptions(exemption):
    """Parse an exemption dictionary and convert to a WHERE clause fragment

    Parameters
    ----------
    exemption: dict
        dictionary with `ruleset` and `words` keys

    Returns
    -------
    tuple[str, list]
        SQL fragment and a list of words that are exempt
    """
    values = exemption["words"]
    exemption_string = (
        f" wordform NOT IN ({','.join(['?' for _ in values])})"
    )
    return exemption_string, values


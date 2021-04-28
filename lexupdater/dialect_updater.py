#!/usr/bin/env python
# coding=utf-8

import sqlite3
import re


class RuleValidator(object):
    """Check that dialect update rules are valid format"""

    def __init__(self, ruledict):
        self._ruledict = ruledict

    def validate(self):
        topkeyset = ["areas", "name", "rules"]
        rulekeyset = ["pattern", "repl", "constraints"]
        conkeyset = ["field", "pattern", "is_regex"]
        if sorted(list(self._ruledict.keys())) != sorted(topkeyset):
            raise KeyError(
                "The dict must have the keys 'area', 'name'"
                " and 'rules', and no other keys"
            )
        for rule in self._ruledict["rules"]:
            if sorted(list(rule.keys())) != sorted(rulekeyset):
                raise KeyError(
                    "The rule dict must have the keys 'pattern',"
                    " 'repl', 'constraints', and no other keys"
                )
            for constraint in rule["constraints"]:
                if sorted(list(constraint.keys())) != sorted(conkeyset):
                    raise KeyError(
                        "The constraint dict must"
                        " have the keys 'field', 'pattern',"
                        " 'is_regex', and no other keys"
                    )


class BlacklistValidator(object):
    """Check that blacklists are valid format"""

    def __init__(self, bldict):
        self._bldict = bldict

    def validate(self):
        blkeys = ["ruleset", "words"]
        if sorted(list(self._bldict.keys())) != sorted(blkeys):
            raise KeyError(
                "The blacklist dict must have the keys"
                " 'ruleset' and 'words', and no other keys"
            )


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
            cstr, cvals = ConstraintReader(
                self._constraints, self._word_table
            ).get_constraints()
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


class ConstraintReader(object):
    """Replacement rules can be constrained to certain grammatical categories
    or other information from the word table. This class reads such constraints
    and converts them to SQL WHERE clauses.
    """

    def __init__(self, constraints, word_table):
        self._word_table = word_table
        self._constraints = constraints
        self._constraintstring = (
            f" WHERE word_id IN (SELECT word_id FROM {self._word_table} WHERE "
        )
        self._values = []

    def _parse_constraints(self):
        for n, const in enumerate(self._constraints):
            field = const["field"]
            pattern = const["pattern"]
            operator = "=" if not const["is_regex"] else "REGEXP"
            self._constraintstring += f"{field} {operator} ?"
            self._values.append(pattern)
            if n != len(self._constraints) - 1:
                self._constraintstring += " AND "

    def get_constraints(self):
        self._parse_constraints()
        return self._constraintstring, self._values


class BlacklistReader(object):
    """parses blacklists and converts them to SQL WHERE clause fragments"""

    def __init__(self, bldict):
        self._bldict = bldict
        BlacklistValidator(bldict).validate()
        self._values = bldict["words"]
        self._blstring = (
            f" wordform NOT IN ("
            f"{','.join(['?' for _ in range(len(self._values))])})"
        )

    def get_blacklist(self):
        return self._blstring, self._values

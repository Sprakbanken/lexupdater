#!/usr/bin/env python
# coding=utf-8
from typing import List


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


def parse_constraints(word_table: str, constraints: List):
    """Extract constraint values from replacement rules
    and construct SQL WHERE queries based on them.

    Grammatical categories and features that are given in the word table of
    the lexicon can be used to narrow down the scope of words that the
    replacement rule applies to.

    Parameters
    ----------
    word_table: str
    constraints: list[dict]
        list of dictionaries with `field`, `pattern`, and `is_regex` keys

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
        SQL fragment, a list of words that are exempt,
        and the ruleset that the exemptions apply to
    """
    ruleset = exemption["ruleset"]
    values = exemption["words"]
    exemption_string = (
        f" wordform NOT IN ({','.join(['?' for _ in values])})"
    )
    return exemption_string, values, ruleset


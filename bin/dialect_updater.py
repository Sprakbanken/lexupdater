#!/usr/bin/env python
# coding=utf-8

import sqlite3
import re


class RuleValidator(object):

    def __init__(self, ruledict):
        self._ruledict = ruledict
    
    def validate(self):
        topkeyset = ["area", "name", "rules"]
        rulekeyset = ["pattern", "repl", "constraints"]
        conkeyset = ["field", "pattern", "is_regex"]
        if sorted(list(self._ruledict.keys())) != sorted(topkeyset):
            raise KeyError("The dict must have the keys 'area', 'name' and 'rules', and no other keys")
        for rule in self._ruledict['rules']:
            if sorted(list(rule.keys())) != sorted(rulekeyset):
                raise KeyError("The rule dict must have the keys 'pattern', 'repl', 'constraints', and no other keys")
            for constraint in rule["constraints"]:
                 if sorted(list(constraint.keys())) != sorted(conkeyset):
                     raise KeyError("The constraint dict must have the keys 'field', 'pattern', 'is_regex', and no other keys")

class BlacklistValidator(object):

    def __init__(self, bldict):
        self._bldict = bldict
    
    def validate(self):
        blkeys = ["ruleset", "words"]
        if sorted(list(self._bldict.keys())) != sorted(blkeys):
            raise KeyError("The blacklist dict must have the keys 'ruleset' and 'words', and no other keys")



class QueryBuiler(object):

    def __init__(self, area, rule):
        self._area = area # Temporary assumption: area per ruleset. Needs to be modified in final version
        self._pattern = rule['pattern']
        self._repl = rule['repl']
        self._constraints = rule['constraints']
        self._constrained_query = True if not self._constraints == [] else False # Affects how the querystring should be continued downstream when blacklist is added


class UpdateQueryBuiler(QueryBuiler):
    def __init__(self, area, rule):
        QueryBuiler.__init__(self, area, rule)
        self._query = f"UPDATE {area} SET nofabet = REGREPLACE(?,?,nofabet)"
        self._values = [self._pattern, self._repl]
        if self._constrained_query == True:
            conststr, constvalues = ConstraintReader(self._constraints).get_constraints()
            self._query += conststr
            self._values = self._values + constvalues
    

    def get_update_query(self):
        return self._query, self._values, self._constrained_query



class SelectQueryBuilder(QueryBuiler):
    pass


class ConstraintReader(object):
    def __init__(self, constraints):
        self._constraints = constraints
        self._constraintstring = " WHERE word_id IN (SELECT word_id FROM words WHERE "
        self._values = []
    
    def _parse_constraints(self):
        for n, const in enumerate(self._constraints):
            field = const['field']
            pattern = const['pattern']
            operator = "=" if const['is_regex'] == False else "REGEXP"
            self._constraintstring += f"{field} {operator} ?"
            self._values.append(pattern)
            if n != len(self._constraints)-1:
                self._constraintstring += " AND "
    
    def get_constraints(self):
        self._parse_constraints()
        return self._constraintstring, self._values

class BlacklistReader(object):
    def __init__(self, bldict):
        self._bldict = bldict
        RuleValidator(bldict).validate()
        self._ruleset = bldict['ruleset']
        self._words = bldict['words']
        #generate queries


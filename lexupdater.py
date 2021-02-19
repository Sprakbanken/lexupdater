#!/usr/bin/env python
# coding=utf-8

import sqlite3
import re

from bin import RuleValidator, UpdateQueryBuiler, SelectQueryBuilder

# Regex checker

def regexp(regpat, item):
    """True if regex match, else False"""
    mypattern = re.compile(regpat)
    return mypattern.search(item) is not None


# Create temporary table_expressions
def create_dialect_table_stmts(dialectlist):
    stmts = []
    for d in dialectlist:
        create_stmt = f'''CREATE TEMPORARY TABLE {d} (
                    pron_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pron_id INTEGER NOT NULL,
                    word_id INTEGER NOT NULL,
                    nofabet TEXT NOT NULL,
                    certainty INTEGER NOT NULL,
                    FOREIGN KEY(word_id) REFERENCES words(word_id) ON UPDATE CASCADE);'''
        insert_stmt = f"INSERT INTO {d} SELECT * FROM base;"
        stmts.append((create_stmt, insert_stmt))
    return stmts


class UpdateDatabase(object):
    def __init__(self, db, rulesets, blacklists=[]):
        self._db = db
        self._rulesets = rulesets
        self._blacklists = blacklists
        self._dialects = ['e_spoken', 'e_written', 'sw_spoken', 'sw_written', 'w_spoken', 'w_written', 
                        't_spoken', 't_written', 'n_spoken', 'n_written']
        for rule in self._rulesets:
            RuleValidator(rule).validate()
    
    def _validate_dialect(self, dialect):
        if not dialect in self._dialects:
            raise ValueError(f"{dialect} is not a valid dialect")
        else:
            return dialect

    def _establish_connection(self):
        self._connection = sqlite3.connect(self._db)
        self._connection.create_function("REGEXP", 2, regexp)
        self._connection.create_function("REGREPLACE", 3, re.sub)
        self._cursor = self._connection.cursor()
        for create_stmt, insert_stmt in create_dialect_table_stmts(self._dialects):
            self._cursor.execute(create_stmt)
            self._cursor.execute(insert_stmt)
            self._connection.commit()
    
    def _construct_update_queries(self):
        self._updates = []
        for ruleset in self._rulesets:
            area = self._validate_dialect(ruleset['area'])
            name = ruleset['name']
            rules = []
            for r in ruleset['rules']:
                mydict = {}
                mydict['query'], mydict['values'], mydict['is_constrained'] = UpdateQueryBuiler(area, r).get_update_query()
                if mydict['is_constrained'] == False:
                    mydict['query'] = mydict['query'] + ';'
                else:
                    mydict['query'] = mydict['query'] + ');' # handle blacklists
                rules.append(mydict)
            self._updates.append(rules)

    def update(self):
        self._establish_connection()
        self._construct_update_queries()
        print(self._cursor.execute("SELECT COUNT(*) FROM e_spoken WHERE nofabet REGEXP ?;", (r'\bAX0 R$',)).fetchall())
        print(self._cursor.execute("SELECT COUNT(*) FROM e_spoken WHERE nofabet REGEXP ?;", (r'\b(R)([NTD])\b',)).fetchall())
        for u in self._updates:
            for rule in u:
                self._cursor.execute(rule['query'], rule['values'])
                self._connection.commit()
        print(self._cursor.execute("SELECT COUNT(*) FROM e_spoken WHERE nofabet REGEXP ?;", (r'\bAX0 R$',)).fetchall())
        print(self._cursor.execute("SELECT COUNT(*) FROM e_spoken WHERE nofabet REGEXP ?;", (r'\b(R)([NTD])\b',)).fetchall())
        self._close_connection()
    
    def _close_connection(self):
        self._connection.close()


# Testing

test1 = {"area": "e_spoken", "name": "retrotest", "rules": 
        [{'pattern': r'\b(R)([NTD])\b', 'repl': r'\1 \2', 'constraints': []}, 
        {'pattern': r'\b(R)(NX0)\b', 'repl': r'\1 AX0 N', 'constraints': []}]}
test2 = {"area": "e_spoken", "name": "masc", "rules": 
        [{'pattern': r'\bAX0 R$', 'repl': r'AA0 R', 'constraints': 
            [{'field': 'pos', 'pattern': 'NN', 'is_regex': False}, {'field': 'feats', 'pattern': r'MAS', 'is_regex': True}]}, 
        {'pattern': r'\bNX0 AX0$', 'repl': r'AA0 N AX0', 'constraints': 
            [{'field': 'pos', 'pattern': 'NN', 'is_regex': False}, {'field': 'feats', 'pattern': r'MAS', 'is_regex': True}]}]}

blacklist1 = {'ruleset': 'masc', 'words': ['søknader', 'søknadene', 'dugnader', 'dugnadene']}


if __name__ == "__main__":
    UpdateDatabase('../backend-db02.db', [test1, test2]).update()
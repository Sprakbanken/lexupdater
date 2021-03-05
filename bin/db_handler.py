#!/usr/bin/env python
# coding=utf-8

import sqlite3
import re

from dialect_updater import RuleValidator, UpdateQueryBuiler, SelectQueryBuilder, BlacklistReader

# Regex checker

def regexp(regpat, item):
    """True if regex match, else False"""
    mypattern = re.compile(regpat)
    return mypattern.search(item) is not None

# Config

dialects =  ['e_spoken', 'e_written', 'sw_spoken', 'sw_written', 'w_spoken', 'w_written', 
            't_spoken', 't_written', 'n_spoken', 'n_written']

word_table = "words_tmp"

database = '../../backend-db02.db'

test1 = {"area": "e_spoken", "name": "retrotest", "rules": 
        [{'pattern': r'\b(R)([NTD])\b', 'repl': r'\1 \2', 'constraints': []}, 
        {'pattern': r'\b(R)(NX0)\b', 'repl': r'\1 AX0 N', 'constraints': []}]}
test2 = {"area": "e_spoken", "name": "masc", "rules": 
        [{'pattern': r'\bAX0 R$', 'repl': r'AA0 R', 'constraints': 
            [{'field': 'pos', 'pattern': r'NN', 'is_regex': False}, {'field': 'feats', 'pattern': r'MAS', 'is_regex': True}]}, 
        {'pattern': r'\bNX0 AX0$', 'repl': r'AA0 N AX0', 'constraints': 
            [{'field': 'pos', 'pattern': r'NN', 'is_regex': False}, {'field': 'feats', 'pattern': r'MAS', 'is_regex': True}]}]}

blacklist1 = {'ruleset': 'retrotest', 'words': ['garn', 'klarne']}
blacklist2 = {'ruleset': 'masc', 'words': ['søknader', 'søknadene', 'dugnader', 'dugnadene']}

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

def create_word_table_stmts(word_table_name):
    create_stmt = f'''CREATE TEMPORARY TABLE {word_table_name} (
                    word_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    wordform TEXT NOT NULL,
                    pos TEXT,
                    feats TEXT,
                    source TEXT,
                    decomp_ort TEXT,
                    decomp_pos TEXT,
                    garbage TEXT,
                    domain TEXT,
                    abbr TEXT,
                    set_name TEXT,
                    style_status TEXT,
                    inflector_role TEXT,
                    inflector_rule TEXT,
                    morph_label TEXT,
                    compounder_code TEXT,
                    update_info TEXT);'''
    insert_stmt = f"INSERT INTO {word_table_name} SELECT * FROM words;"
    return create_stmt, insert_stmt



class UpdateDatabase(object):
    def __init__(self, db, rulesets, dialect_names, word_tbl, blacklists=[]):
        self._db = db
        self._rulesets = rulesets
        self._blacklists = blacklists
        self._dialects = dialect_names
        self._word_table = word_tbl
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
        self._word_create_stmt, self._word_update_stmt = create_word_table_stmts(self._word_table)
        self._cursor.execute(self._word_create_stmt)
        self._cursor.execute(self._word_update_stmt)
        self._connection.commit()
        for create_stmt, insert_stmt in create_dialect_table_stmts(self._dialects):
            self._cursor.execute(create_stmt)
            self._cursor.execute(insert_stmt)
            self._connection.commit()
    
    def _construct_update_queries(self):
        self._updates = []
        for ruleset in self._rulesets:
            name = ruleset["name"]
            area = self._validate_dialect(ruleset['area'])
            self._bl_str = ''
            self._bl_values = []
            for blist in self._blacklists:
                if blist['ruleset'] == name:
                    self._bl_str, self._bl_values = BlacklistReader(blist).get_blacklist()
                    break # Possibly add support for myltiple backlists referencing the same ruleset 
            rules = []
            for r in ruleset['rules']:
                mydict = {}
                mydict['query'], mydict['values'], mydict['is_constrained'] = UpdateQueryBuiler(area, r, self._word_table).get_update_query()
                if mydict['is_constrained'] == False:
                    if self._bl_str == '':
                        mydict['query'] = mydict['query'] + ';'
                    else:
                        mydict['query'] = mydict['query'] + f' WHERE word_id IN (SELECT word_id FROM {self._word_table} WHERE' + self._bl_str + ');'
                        mydict['values'] = mydict['values'] + self._bl_values
                else:
                    if self._bl_str == '':
                        mydict['query'] = mydict['query'] + ');'
                    else:
                        mydict['query'] = mydict['query'] + ' AND' + self._bl_str + ');'
                        mydict['values'] = mydict['values'] + self._bl_values
                rules.append(mydict)
            self._updates.append(rules)
        


    def update(self):
        self._fullqueries = []
        self._establish_connection()
        self._construct_update_queries()
        for u in self._updates:
            for rule in u:
                self._cursor.execute(rule['query'], tuple(rule['values']))
                self._connection.commit()
                self._fullqueries.append((rule['query'], tuple(rule['values'])))
#        self.close_connection()
#        return self._fullqueries # embed call in a print to manually verify the correctness of the update statements
    
    def get_connection(self):
        return self._connection
    
    def close_connection(self):
        self._connection.close()

class Results(object):
    def __init__(self, connection, dialect_names, word_tbl):
        self._connection = connection
        self._cursor = self._connection.cursor()
        self._dialects = dialect_names
        self._word_table = word_tbl
        self._results = {d:[] for d in self._dialects}
        self._query_db()
    
    def _query_db(self):
        for d in self._dialects:
            stmt = f"""SELECT w.word_id, w.wordform, w.pos, w.feats, w.source, w.decomp_ort, w.decomp_pos, 
                        w.garbage, w.domain, w.abbr, w.set_name, w.style_status, w.inflector_role, w.inflector_rule, 
                        w.morph_label, w.compounder_code, w.update_info, p.pron_id, p.nofabet, p.certainty
                        FROM {self._word_table} w LEFT JOIN {d} p ON p.word_id = w.word_id;"""
            self._results[d] = self._cursor.execute(stmt).fetchall()
    
    def get_results(self):
        return self._results


if __name__ == "__main__":
    updateobj = UpdateDatabase(database, [test1, test2], dialects, word_table, blacklists=[blacklist1, blacklist2])
    updateobj.update()
    connection = updateobj.get_connection()
    resultobj = Results(connection, dialects, word_table)
    updateobj.close_connection()
    resultobj2 = Results(connection, dialects, word_table)
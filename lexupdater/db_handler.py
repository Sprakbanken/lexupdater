#!/usr/bin/env python
# coding=utf-8

import sqlite3
import re

from .dialect_updater import RuleValidator, UpdateQueryBuilder, SelectQueryBuilder, BlacklistReader

# Regex checker, to be used in SQL queries

def regexp(regpat, item):
    """True if regex match, else False"""
    mypattern = re.compile(regpat)
    return mypattern.search(item) is not None


# Create temporary table_expressions

def create_dialect_table_stmts(dialectlist):
    """Create a temp table for each dialect in the dialect list
    (to be supplied from the config file), and make it mirror base, 
    the table containing the original pronunciations."""
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
    """Create a temp table that mirrors the "words" table,
    i.e. the table with ortographic forms and word metadata.
    The name should be supplied in the configuration file. 
    New words should be added to this table."""
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



class DatabaseUpdater(object):
    """Class for handling the db connection and running the updates on temp tables"""
    def __init__(self, db, rulesets, dialect_names, word_tbl, blacklists=[]):
        self._db = db
        self._rulesets = rulesets
        self._blacklists = blacklists
        self._dialects = dialect_names
        self._word_table = word_tbl
        for rule in self._rulesets:
            RuleValidator(rule).validate()
        self._establish_connection()
    
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
            dialects = [self._validate_dialect(dialect) for dialect in ruleset['areas']] # issue 2: handle list input
            self._bl_str = ''
            self._bl_values = []
            for blist in self._blacklists:
                if blist['ruleset'] == name:
                    self._bl_str, self._bl_values = BlacklistReader(blist).get_blacklist()
                    break # Possibly add support for multiple backlists referencing the same ruleset 
            rules = []
            for r in ruleset['rules']:
                for dialect in dialects:
                    mydict = {}
                    mydict['query'], mydict['values'], mydict['is_constrained'] = UpdateQueryBuilder(dialect, r, self._word_table).get_update_query()
                    if mydict['is_constrained'] == False: # issue 2: handle multiple queries
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
        """Connects to db and creates temp tables. Then reads dialect update rules and applies them to the temp tables."""
        self._fullqueries = []
        self._establish_connection()
        self._construct_update_queries()
#        print(self._cursor.execute(f"SELECT w.wordform, p.nofabet FROM {self._word_table} w LEFT JOIN e_spoken p ON w.word_id = p.word_id WHERE wordform = 'barn';").fetchall())
        for u in self._updates:
            for rule in u:
                self._cursor.execute(rule['query'], tuple(rule['values']))
                self._connection.commit()
                self._fullqueries.append((rule['query'], tuple(rule['values'])))
#        print(self._cursor.execute(f"SELECT w.wordform, p.nofabet FROM {self._word_table} w LEFT JOIN e_spoken p ON w.word_id = p.word_id WHERE wordform = 'barn';").fetchall())
        return self._fullqueries # embed call in a print to manually verify the correctness of the update statements
    
    def get_connection(self):
        return self._connection

    def get_results(self):
        """Retrieves a dict with the updated state of the lexicon for each dialect."""
        self._results = {d:[] for d in self._dialects}
        for d in self._dialects:
            stmt = f"""SELECT w.word_id, w.wordform, w.pos, w.feats, w.source, w.decomp_ort, w.decomp_pos, 
                        w.garbage, w.domain, w.abbr, w.set_name, w.style_status, w.inflector_role, w.inflector_rule, 
                        w.morph_label, w.compounder_code, w.update_info, p.pron_id, p.nofabet, p.certainty
                        FROM {self._word_table} w LEFT JOIN {d} p ON p.word_id = w.word_id;"""
            self._results[d] = self._cursor.execute(stmt).fetchall()
        return self._results
    
    def close_connection(self):
        self._connection.close()
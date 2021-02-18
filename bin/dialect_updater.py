#!/usr/bin/env python
# coding=utf-8

import sqlite3
import re

# Regex functions

def regexp(regpat, item):
    """True if regex match, else False"""
    mypattern = re.compile(regpat)
    return mypattern.search(item) is not None


class QueryBuiler(object):

    def __init__(self, connection, ruledict):
        self._connection = connection
        self._cursor = self._connection.cursor()
        self._parse_ruledict(ruledict)
    
    def _parse_ruledict(self, mydict):
        topkeyset = ["area", "name", "rules"]
        rulekeyset = ["pattern", "repl", "context"]
        if list(mydict.keys()).sort() != topkeyset.sort():
            raise KeyError("The dict must have the keys 'area', 'name' and 'rules', and no other keys")
        for rule in mydict['rules']:
            if list(rule.keys()).sort() != rulekeyset.sort():
                raise KeyError("The rule dict must have the keys 'pattern', 'repl', 'context', and no other keys")
        self._area = mydict['area'] # Add sanity check of this field
        self._rules = mydict['rules'] # Add sanity check of context
        self._name = mydict['name'] #Use to reference rule in whitelist and possibly elsewhere
    
    def _read_rule(self, rule):
        placeholder = [rule['pattern'], rule['repl']]
        update_stmt = f"UPDATE {self._area} SET nofabet = REGREPLACE(?,?,nofabet)"
        if rule['context'] != []:
            whereclause = " WHERE word_id IN (SELECT word_id FROM words WHERE "
            for n, context in enumerate(rule['context']):
                field = context['field']
                pattern = context['pattern']
                operator = "=" if context['regex'] == False else "REGEXP"
                whereclause += f"{field} {operator} ?"
                placeholder.append(pattern)
                if n == len(rule['context'])-1:
                    whereclause += ")"
                else:
                    whereclause += " AND "
            update_stmt += whereclause
        print(update_stmt+"; , "+ str(tuple(placeholder)) + "\n\n")
        return tuple(placeholder), update_stmt+";"
    
    def run_rules(self):
        for rule in self._rules:
            read = self._read_rule(rule)
            replpair = read[0]
            update_stmt = read[1]
            self._cursor.execute(update_stmt, replpair)
            self._connection.commit()




if __name__ == "__main__":
    try:
        sqliteConnection = sqlite3.connect('../../backend-db02.db')
        sqliteConnection.create_function("REGEXP", 2, regexp)
        sqliteConnection.create_function("REGREPLACE", 3, re.sub)
        cursor = sqliteConnection.cursor()
        print("Successfully Connected to SQLite")
        # Run tests
        create_dialect_table = '''CREATE TEMPORARY TABLE dialect_x (
                    pron_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pron_id INTEGER NOT NULL,
                    word_id INTEGER NOT NULL,
                    nofabet TEXT NOT NULL,
                    certainty INTEGER NOT NULL,
                    FOREIGN KEY(word_id) REFERENCES words(word_id) ON UPDATE CASCADE);'''
        cursor.execute(create_dialect_table)
        cursor.execute("INSERT INTO dialect_x SELECT * FROM base;")
        sqliteConnection.commit(), 

        test1 = {"area": "dialect_x", "name": "retrotest", "rules": 
                [{'pattern': r'\b(R)([NTD])\b', 'repl': r'\1 \2', 'context': []}, 
                {'pattern': r'\b(R)(NX0)\b', 'repl': r'\1 AX0 N', 'context': []}]}
        test2 = {"area": "dialect_x", "name": "masc", "rules": 
                [{'pattern': r'\bAX0 R$', 'repl': r'AA0 R', 'context': 
                    [{'field': 'pos', 'pattern': 'NN', 'regex': False}, {'field': 'feats', 'pattern': r'MAS', 'regex': True}]}, 
                {'pattern': r'\bNX0 AX0$', 'repl': r'AA0 N AX0', 'context': 
                    [{'field': 'pos', 'pattern': 'NN', 'regex': False}, {'field': 'feats', 'pattern': r'MAS', 'regex': True}]}]}
        print(cursor.execute("SELECT COUNT(*) FROM dialect_x WHERE nofabet REGEXP ?;", (r'\bAX0 R$',)).fetchall())
        print(cursor.execute("SELECT word_id FROM words WHERE pos = ? AND feats REGEXP ?;", ('NN', 'MAS')).fetchall())
        builder = QueryBuiler(sqliteConnection, test1)
        builder.run_rules()
        builder2 = builder = QueryBuiler(sqliteConnection, test2)
        builder2.run_rules()
        print(cursor.execute("SELECT COUNT(*) FROM dialect_x WHERE nofabet REGEXP ?;", (r'\bAX0 R$',)).fetchall())
        print(cursor.execute("""SELECT w.wordform, p.nofabet FROM words w 
                            LEFT JOIN dialect_x p ON w.word_id = p.word_id 
                            WHERE wordform = 'brekker' OR wordform = 'gutter' 
                            OR wordform = 'kvinner';""").fetchall())


    except sqlite3.Error as error:
        print("Error while creating a sqlite table", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()
            print("sqlite connection is closed")
#!/usr/bin/env python
# coding=utf-8

import sqlite3
import re

# Regex functions

def regexp(regpat, item):
    """True if regex match, else False"""
    mypattern = re.compile(regpat)
    return mypattern.match(item) is not None

def regreplace(pattern, rep, item):
    """Replace regex pattern with substitution"""
    mypattern = re.compile(pattern)
    return mypattern.sub(rep, item)

class QueryBuiler(object):

    def __init__(self, db):
        self._connection = sqlite3.connect(db)
        self._cursor = self._connection.cursor()



if __name__ == "__main__":
    try:
        sqliteConnection = sqlite3.connect('../../backend-db_test.db')
        print("Successfully Connected to SQLite")
        # Run tests

    except sqlite3.Error as error:
        print("Error while creating a sqlite table", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()
            print("sqlite connection is closed")
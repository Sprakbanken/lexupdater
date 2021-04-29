#!/usr/bin/env python
# coding=utf-8

import re
import sqlite3

from schema import Schema

from .config import rule_schema, exemption_schema, dialect_schema
from .dialect_updater import (
    UpdateQueryBuilder,
    SelectQueryBuilder,
    ExemptionReader,
)


# Regex checker, to be used in SQL queries


def regexp(regpat, item):
    """True if regex match, else False."""
    mypattern = re.compile(regpat)
    return mypattern.search(item) is not None


# Create temporary table_expressions


def create_dialect_table_stmts(dialectlist):
    """Create a temp table for each dialect in the dialect list
    (to be supplied from the config file), and make it mirror base,
    the table containing the original pronunciations.
    """
    stmts = []
    for d in dialectlist:
        create_stmt = f"""CREATE TEMPORARY TABLE {d} (
                    pron_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pron_id INTEGER NOT NULL,
                    word_id INTEGER NOT NULL,
                    nofabet TEXT NOT NULL,
                    certainty INTEGER NOT NULL,
                    FOREIGN KEY(word_id) REFERENCES words(word_id)
                    ON UPDATE CASCADE);"""
        insert_stmt = f"INSERT INTO {d} SELECT * FROM base;"
        stmts.append((create_stmt, insert_stmt))
    return stmts


def create_word_table_stmts(word_table_name):
    """Create a temp table that mirrors the "words" table,
    i.e. the table with ortographic forms and word metadata.
    The name should be supplied in the configuration file.
    New words should be added to this table.
    """
    create_stmt = f"""CREATE TEMPORARY TABLE {word_table_name} (
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
                    update_info TEXT);"""
    insert_stmt = f"INSERT INTO {word_table_name} SELECT * FROM words;"
    return create_stmt, insert_stmt


class DatabaseUpdater(object):
    """Class for handling the db connection and
    running the updates on temp tables.
    """

    def __init__(self, db, rulesets, dialect_names, word_tbl, exemptions=None):
        if exemptions is None:
            exemptions = []
        self._db = db
        # Validate the config values before instantiating the DatabaseUpdater
        self._rulesets = rule_schema.validate(rulesets)
        self._exemptions = exemption_schema.validate(exemptions)
        self._dialects = dialect_schema.validate(dialect_names)
        self._word_table = word_tbl
        self._establish_connection()

    def validate_dialects(self, ruleset_dialects):
        return Schema(self._dialects).validate(ruleset_dialects)

    def _establish_connection(self):
        self._connection = sqlite3.connect(self._db)
        self._connection.create_function("REGEXP", 2, regexp)
        self._connection.create_function("REGREPLACE", 3, re.sub)
        self._cursor = self._connection.cursor()
        (self._word_create_stmt, self._word_update_stmt) = create_word_table_stmts(
            self._word_table
        )
        self._cursor.execute(self._word_create_stmt)
        self._cursor.execute(self._word_update_stmt)
        self._connection.commit()
        dialect_stmts = create_dialect_table_stmts(self._dialects)
        for create_stmt, insert_stmt in dialect_stmts:
            self._cursor.execute(create_stmt)
            self._cursor.execute(insert_stmt)
            self._connection.commit()

    def _construct_update_queries(self):
        # TODO: refactor to handle variable updates in separate functions
        self._updates = []
        for ruleset in self._rulesets:
            name = ruleset["name"]
            rule_dialects = self.validate_dialects(ruleset["areas"])
            self._bl_str = ""
            self._bl_values = []
            for blist in self._exemptions:
                if blist["ruleset"] == name:
                    blreader = ExemptionReader(blist).get_blacklist()
                    self._bl_str, self._bl_values = blreader
                    break
            rules = []
            for r in ruleset["rules"]:
                for dialect in rule_dialects:
                    builder = UpdateQueryBuilder(
                        dialect, r, self._word_table
                    ).get_update_query()
                    mydict = {
                        "query": builder[0],
                        "values": builder[1],
                        "is_constrained": builder[2],
                    }
                    if not mydict["is_constrained"]:
                        if self._bl_str == "":
                            mydict["query"] = mydict["query"] + ";"
                        else:
                            mydict["query"] = (
                                f"{mydict['query']} "
                                f"WHERE word_id IN "
                                f"(SELECT word_id "
                                f"FROM {self._word_table} "
                                f"WHERE{self._bl_str});"
                            )
                            mydict["values"] = mydict["values"] + self._bl_values
                    else:
                        if self._bl_str == "":
                            mydict["query"] = mydict["query"] + ");"
                        else:
                            mydict["query"] = (
                                mydict["query"] + " AND" + self._bl_str + ");"
                            )
                            mydict["values"] = mydict["values"] + self._bl_values
                    rules.append(mydict)
            self._updates.append(rules)

    def update(self):
        """Connects to db and creates temp tables. Then reads dialect
        update rules and applies them to the temp tables.
        """
        self._fullqueries = []
        self._establish_connection()
        self._construct_update_queries()
        for u in self._updates:
            for rule in u:
                self._cursor.execute(rule["query"], tuple(rule["values"]))
                self._connection.commit()
                self._fullqueries.append((rule["query"], tuple(rule["values"])))
        return self._fullqueries  # Test: embed call in a print

    def get_connection(self):
        return self._connection

    def get_results(self):
        """Retrieves a dict with the updated state of the lexicon for
        each dialect.
        """
        self._results = {d: [] for d in self._dialects}
        for d in self._dialects:
            stmt = f"""SELECT w.word_id, w.wordform, w.pos, w.feats, w.source,
                    w.decomp_ort, w.decomp_pos,w.garbage, w.domain, w.abbr,
                    w.set_name, w.style_status, w.inflector_role,
                    w.inflector_rule, w.morph_label, w.compounder_code,
                    w.update_info, p.pron_id, p.nofabet, p.certainty
                    FROM {self._word_table} w
                    LEFT JOIN {d} p ON p.word_id = w.word_id;"""
            self._results[d] = self._cursor.execute(stmt).fetchall()
        return self._results

    def close_connection(self):
        self._connection.close()

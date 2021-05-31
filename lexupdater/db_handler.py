#!/usr/bin/env python
# coding=utf-8

"""Connect to and update the database containing the pronunciation lexicon."""
import logging
import re
import sqlite3

from .config.constants import (
    dialect_schema,
    CREATE_DIALECT_TABLE_STMT,
    CREATE_WORD_TABLE_STMT,
    INSERT_STMT,
    UPDATE_QUERY,
    WHERE_WORD_IN_STMT,
    SELECT_WORDS_QUERY,
)
from .dialect_updater import parse_rules


def regexp(reg_pat, item):
    """Check whether a regex pattern matches a string item.

    To be used in SQL queries.

    Parameters
    ----------
    reg_pat: str
        regex pattern, typically an r-string
    item: str

    Returns
    -------
    bool
        True if reg_pat matches item, else False.
    """
    reg_pattern = re.compile(reg_pat)
    return reg_pattern.search(item) is not None


class DatabaseUpdater:
    """Handler of the db connection.

    Applies updates on temporary tables.

    Parameters
    ----------
    db: str
        Name of database to connect to, e.g. file path to the local db on disk
    rulesets: list
        List of ruleset dictionaries, which are validated with
        rule_schema from the config.constants module
    dialect_names: list
        List of dialects to update transcription entries for
    word_tbl: str
        Name of temporary table to be created for the word entries
    exemptions:
        List of exemption dictionaries, containing words
        that are exempt from a given ruleset, and the name of the ruleset
    """

    def __init__(self, db, rulesets, dialect_names, word_tbl, exemptions=None):
        """Set object attributes, connect to db and create temp tables."""
        if exemptions is None:
            exemptions = []
        self._db = db
        self.word_table = word_tbl
        self.dialects = dialect_schema.validate(dialect_names)
        self.parsed_rules = parse_rules(
            rulesets,
            self.dialects,
            exemptions
        )
        self.results = {dialect: [] for dialect in self.dialects}
        self._establish_connection()

    def _establish_connection(self):
        """Connect to db and create temporary tables."""
        self._connection = sqlite3.connect(self._db)
        self._connection.create_function("REGEXP", 2, regexp)
        self._connection.create_function("REGREPLACE", 3, re.sub)
        self._cursor = self._connection.cursor()
        self._cursor.execute(
            CREATE_WORD_TABLE_STMT.format(word_table_name=self.word_table)
        )
        self._cursor.execute(
            INSERT_STMT.format(table_name=self.word_table, other_table="words")
        )
        self._connection.commit()
        for dialect in self.dialects:
            create_stmt = CREATE_DIALECT_TABLE_STMT.format(dialect=dialect)
            self._cursor.execute(create_stmt)
            insert_stmt = INSERT_STMT.format(
                table_name=dialect,
                other_table="base"
            )
            self._cursor.execute(insert_stmt)
            self._connection.commit()

    def select_words_matching_rules(self):
        """Apply a SELECT SQL query for each rule.

        Construct the SQL query with values from the rules and exemptions
        before applying it.
        """
        # The replacement string _ is not used for this query
        for dialect, pattern, _, conditional, conditions in self.parsed_rules:
            where_word = WHERE_WORD_IN_STMT.format(
                word_table=self.word_table, conditions=conditional
            ) if conditional else ""

            query = SELECT_WORDS_QUERY.format(
                        word_table=self.word_table,
                        dialect=dialect,
                        where_word_in_stmt=where_word
                    )
            values = tuple([pattern] + conditions)
            word_match = self._cursor.execute(query, values).fetchall()
            logging.info(f"Words affected by {values[0]}: {word_match}")
            self.results[dialect] = word_match

    def update(self):
        """Apply SQL UPDATE queries to the dialect temp tables.

        Fill in the query templates with the rules and exemptions before
        applying them.
        """
        for dialect, pattern, replacement, conditional, conditions in \
                self.parsed_rules:
            where_word = WHERE_WORD_IN_STMT.format(
                word_table=self.word_table, conditions=conditional
            ) if conditional else ""
            query = UPDATE_QUERY.format(
                dialect=dialect,
                where_word_in_stmt=where_word
            )
            values = tuple([pattern, replacement] + conditions)
            self._cursor.execute(query, values)
            self._connection.commit()
            self.update_results()

    def get_connection(self):
        """Return the object instance's sqlite3 connection."""
        return self._connection

    def update_results(self):
        """Fetch the state of the lexicon for each dialect.

        Returns
        -------
        results: dict
            Dialect names are keys, and the resulting collection of values
            from each field in the database are the values
        """
        for dialect in self.dialects:
            stmt = f"""SELECT w.word_id, w.wordform, w.pos, w.feats, w.source,
                    w.decomp_ort, w.decomp_pos, w.garbage, w.domain, w.abbr,
                    w.set_name, w.style_status, w.inflector_role,
                    w.inflector_rule, w.morph_label, w.compounder_code,
                    w.update_info, p.pron_id, p.nofabet, p.certainty
                    FROM {self.word_table} w
                    LEFT JOIN {dialect} p ON p.word_id = w.word_id;"""
            self.results[dialect] = self._cursor.execute(stmt).fetchall()

    def close_connection(self):
        """Close the object instance's sqlite3 connection."""
        self._connection.close()

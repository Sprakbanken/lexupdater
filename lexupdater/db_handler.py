#!/usr/bin/env python
# coding=utf-8

"""Connect to and update the database containing the pronunciation lexicon."""

import logging
import re
import sqlite3

from .constants import (
    dialect_schema,
    CREATE_PRON_TABLE_STMT,
    CREATE_WORD_TABLE_STMT,
    INSERT_STMT,
    UPDATE_QUERY,
    WHERE_WORD_IN_STMT,
    SELECT_QUERY,
    COL_WORD_PRON,
    WHERE_REGEXP,
    COL_WORD_POS_FEATS_PRON,
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
    exemptions:
        List of exemption dictionaries, containing words
        that are exempt from a given ruleset, and the name of the ruleset
    """

    def __init__(self, db, rulesets, dialect_names, exemptions=None):
        """Set object attributes, connect to db and create temp tables."""
        if exemptions is None:
            exemptions = []
        self._db = db
        self.word_table = "words_tmp"
        self.pron_table = "pron_tmp"
        self.dialects = dialect_schema.validate(dialect_names)
        self.parsed_rules = parse_rules(
            self.dialects,
            rulesets,
            exemptions
        )
        self.results = {dialect: [] for dialect in self.dialects}
        self._connect_and_populate()

    def _connect_and_populate(self):
        """Connect to db. Create and populate temp tables."""
        logging.debug("Connecting to the database %s", self._db)
        self._connection = sqlite3.connect(self._db)
        self._connection.create_function("REGEXP", 2, regexp)
        self._connection.create_function("REGREPLACE", 3, re.sub)
        self._cursor = self._connection.cursor()
        self._create_temp_tables()
        self._populate_temp_tables()
        self._create_and_populate_dialect_tables()

    def _create_temp_tables(self):
        logging.debug(
            "Creating temporary tables: word_table, pron_table"
        )
        self._cursor.execute(
            CREATE_WORD_TABLE_STMT.format(
                word_table_name=self.word_table
            )
        )
        self._cursor.execute(
            CREATE_PRON_TABLE_STMT.format(
                pron_table_name=self.pron_table
            )
        )
        self._connection.commit()

    def _populate_temp_tables(self):
        logging.debug(
            "Populating temporary tables: word_table, pron_table"
        )
        self._cursor.execute(
            INSERT_STMT.format(
                table_name=self.word_table,
                other_table="words"
            )
        )
        self._cursor.execute(
            INSERT_STMT.format(
                table_name=self.pron_table, other_table="base"
            )
        )
        self._connection.commit()

    def _create_and_populate_dialect_tables(self):
        logging.debug("Creating and populating dialect tables")
        for dialect in self.dialects:
            create_stmt = CREATE_PRON_TABLE_STMT.format(
                pron_table_name=dialect
            )
            self._cursor.execute(create_stmt)
            insert_stmt = INSERT_STMT.format(
                table_name=dialect,
                other_table=self.pron_table
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
            where_word = re.sub(
                "WHERE unique_id",
                "AND w.unique_id",
                WHERE_WORD_IN_STMT.format(
                    word_table=self.word_table, conditions=conditional
                ),
                1
            ) if conditional else ""

            query = SELECT_QUERY.format(
                columns=COL_WORD_PRON,
                word_table=self.word_table,
                pron_table=dialect,
                where_regex=WHERE_REGEXP,
                where_word_in_stmt=where_word
            )
            values = tuple([pattern] + conditions)
            logging.debug("Execute SQL Query: %s %s", query, values)
            word_match = self._cursor.execute(query, values).fetchall()
            logging.info(
                "Regex pattern '%s' covers %s matching words for dialect %s",
                pattern,
                len(word_match),
                dialect
            )
            self.results[dialect] += [(pattern, word_match)]

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
            logging.debug("Execute SQL Query: %s %s", query, values)
            self._cursor.execute(query, values)
            self._connection.commit()
        self.update_results()

    def update_results(self):
        """Assign updated lexicon state to the results attribute.

        For each dialect, fetch the state of the lexicon
        after the rules have been applied,
        and update the results dictionary with the new values.

        results: dict
            Dialect names are keys, and the resulting collection of values
            from each field in the database are the values
        """
        for dialect in self.dialects:
            stmt = SELECT_QUERY.format(
                columns=COL_WORD_POS_FEATS_PRON,
                word_table=self.word_table,
                pron_table=dialect,
                where_regex='',
                where_word_in_stmt=''
            )
            self.results[dialect] = self._cursor.execute(stmt).fetchall()
            logging.debug("Update results for %s ", dialect)

    def get_base(self):
        """Select the state of the lexicon before the updates.

        Returns
        -------
        result: list
            The full contents of the base lexicon
        """
        stmt = SELECT_QUERY.format(
                columns=COL_WORD_POS_FEATS_PRON,
                word_table="words",
                pron_table="base",
                where_regex='',
                where_word_in_stmt=''
            )
        result = self._cursor.execute(stmt).fetchall()
        logging.debug(
            "Fetched %s results from the base lexicon with SQL query: \n%s ",
            len(result),
            stmt
        )
        return result

    def get_connection(self):
        """Return the object instance's sqlite3 connection."""
        return self._connection

    def close_connection(self):
        """Close the object instance's sqlite3 connection."""
        self._connection.close()

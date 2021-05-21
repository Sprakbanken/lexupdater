#!/usr/bin/env python
# coding=utf-8

"""
Connect to and update the sqlite3 database
which contains the pronunciation lexicon.
"""

import re
import sqlite3

from .config.constants import rule_schema, exemption_schema, dialect_schema
from .dialect_updater import (
    map_rule_exemptions,
    parse_exemptions,
    parse_constraints,
)

CREATE_DIALECT_TABLE_STMT = """CREATE TEMPORARY TABLE {dialect} (
pron_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
pron_id INTEGER NOT NULL,
word_id INTEGER NOT NULL,
nofabet TEXT NOT NULL,
certainty INTEGER NOT NULL,
FOREIGN KEY(word_id) REFERENCES words(word_id)
ON UPDATE CASCADE);
"""

CREATE_WORD_TABLE_STMT = """CREATE TEMPORARY TABLE {word_table_name} (
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

INSERT_STMT = "INSERT INTO {table_name} SELECT * FROM {other_table};"

UPDATE_QUERY = (
    "UPDATE {dialect} SET nofabet = REGREPLACE(?,?,nofabet) "
    "{where_word_in_stmt};"
)

WHERE_WORD_IN_STMT = (
    "WHERE word_id IN (SELECT word_id FROM {word_table} "
    "WHERE {constraints}{exemptions})"
)


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
    """Class for handling the db connection and
    running the updates on temp tables.

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
        if exemptions is None:
            exemptions = []
        self._db = db
        self._word_table = word_tbl
        # Validate the config values before assigning the attributes
        self._rulesets = rule_schema.validate(rulesets)
        self._exemptions = exemption_schema.validate(exemptions)
        self._dialects = dialect_schema.validate(dialect_names)
        self._establish_connection()

    def validate_dialects(self, ruleset_dialects):
        """Filter ruleset_dialects by the class instance _dialects attribute"""
        valid_dialects = [d for d in ruleset_dialects if d in self._dialects]
        return valid_dialects

    def _establish_connection(self):
        """Connect to db and create temporary tables for the transformation
        rules to be applied on.
        """
        self._connection = sqlite3.connect(self._db)
        self._connection.create_function("REGEXP", 2, regexp)
        self._connection.create_function("REGREPLACE", 3, re.sub)
        self._cursor = self._connection.cursor()
        self._cursor.execute(
            CREATE_WORD_TABLE_STMT.format(word_table_name=self._word_table)
        )
        self._cursor.execute(
            INSERT_STMT.format(table_name=self._word_table, other_table="words")
        )
        self._connection.commit()
        for dialect in self._dialects:
            create_stmt = CREATE_DIALECT_TABLE_STMT.format(dialect=dialect)
            self._cursor.execute(create_stmt)
            insert_stmt = INSERT_STMT.format(
                table_name=dialect,
                other_table="base"
            )
            self._cursor.execute(insert_stmt)
            self._connection.commit()

    def construct_update_queries(self):
        """Create sqlite3 update queries for the rules in
        self._rulesets, in order to update the relevant entries.

        The "query" strings contain SQL-style formatting variables "?",
        which are replaced with the strings in the "values" tuple,
        in positional order,
        when they are executed with the sqlite3 db connection cursor.

        Yields
        ------
        tuple[str, list[str]]
            query: the update query with "?" placeholders
            values: list of positional values to be slotted into placeholders
        """

        rule_exemptions = map_rule_exemptions(self._exemptions)

        for ruleset in self._rulesets:
            rule_name = ruleset["name"]
            rule_dialects = self.validate_dialects(ruleset["areas"])
            if not rule_dialects:
                continue

            exempt_words = rule_exemptions.get(rule_name, [])
            exempt_str = parse_exemptions(exempt_words)

            for rule in ruleset["rules"]:

                constraints = rule["constraints"]
                is_constrained = bool(constraints)
                constraint_str, constraint_values = parse_constraints(
                    constraints)

                values = [rule["pattern"], rule["repl"]]
                values += constraint_values + exempt_words

                if not is_constrained and not exempt_words:
                    where_word_in_stmt = ""
                else:
                    where_word_in_stmt = WHERE_WORD_IN_STMT.format(
                        word_table=self._word_table,
                        constraints=constraint_str,
                        exemptions=(
                            f" AND {exempt_str}"
                            if is_constrained and exempt_str
                            else exempt_str
                        )
                    )

                for dialect in rule_dialects:
                    yield (
                        UPDATE_QUERY.format(
                            dialect=dialect,
                            where_word_in_stmt=where_word_in_stmt
                        ),
                        tuple(values)
                    )

    def update(self):
        """Apply SQL update queries to the dialect temp tables.

        Generate the queries with the configured rules and
        exemptions before applying them.
        """
        updates = self.construct_update_queries()
        for query, values in updates:
            self._cursor.execute(query, values)
            self._connection.commit()

    def get_connection(self):
        """Return the object instance's sqlite3 connection."""
        return self._connection

    def get_results(self):
        """Fetch the state of the lexicon for each dialect

        Returns
        -------
        results: dict
            Dialect names are keys, and the resulting collection of values
            from each field in the database are the values
        """
        results = {dialect: [] for dialect in self._dialects}
        for dialect in self._dialects:
            stmt = f"""SELECT w.word_id, w.wordform, w.pos, w.feats, w.source,
                    w.decomp_ort, w.decomp_pos, w.garbage, w.domain, w.abbr,
                    w.set_name, w.style_status, w.inflector_role,
                    w.inflector_rule, w.morph_label, w.compounder_code,
                    w.update_info, p.pron_id, p.nofabet, p.certainty
                    FROM {self._word_table} w
                    LEFT JOIN {dialect} p ON p.word_id = w.word_id;"""
            results[dialect] = self._cursor.execute(stmt).fetchall()
        return results

    def close_connection(self):
        """Close the object instance's sqlite3 connection."""
        self._connection.close()

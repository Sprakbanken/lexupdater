"""Connect to and update the database containing the pronunciation lexicon."""
from collections import defaultdict
import logging
import re
import sqlite3

from .rule_objects import construct_rulesets
from .constants import (
    dialect_schema,
    CREATE_PRON_TABLE_STMT,
    CREATE_WORD_TABLE_STMT,
    INSERT_STMT,
    UPDATE_QUERY,
    WHERE_WORD_IN_STMT,
    SELECT_QUERY,
    COL_WORD_PRON_ID,
    WHERE_REGEXP,
    COL_WORD_POS_FEATS_PRON,
    COL_ID_WORD_FEATS_PRON_ID,
    NEWWORD_INSERT,
    NW_WORD_COLS,
    NW_PRON_COLS,
)
from .dialect_updater import parse_conditions
from .newword_updater import parse_newwords


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

    Construct queries with the input data, apply them to the database, and return the results.

    Parameters
    ----------
    db: str
        Name of database to connect to, e.g. file path to the local db on disk
    rulesets: list
        List of ruleset dictionaries, which are validated with
        rule_schema from the config.constants module
    temp_tables: list
        List of dialects to update transcription entries for
    exemptions:
        List of exemption dictionaries, containing words
        that are exempt from a given ruleset, and the name of the ruleset
    """

    def __init__(
            self, db, temp_tables, rulesets=None, newwords=None, exemptions=None):
        """Set object attributes, connect to db and create temp tables."""
        self._db = db
        self.word_table = "words_tmp"
        self.pron_table = "pron_tmp"
        self.dialects = dialect_schema.validate(temp_tables)
        self._rulesets = []
        self._exemptions = [] if exemptions is None else exemptions
        self._newwords = newwords
        if rulesets is not None:
            self.rulesets = rulesets
        self._connect_and_populate()

    @property
    def rulesets(self):
        """List of ruleset objects."""
        return self._rulesets

    @rulesets.setter
    def rulesets(self, new_rulesets):
        self._rulesets = construct_rulesets(new_rulesets, self.exemptions, self.dialects)

    @property
    def exemptions(self):
        """List of exemption dicts."""
        return self._exemptions

    @exemptions.setter
    def exemptions(self, new_exemptions):
        self._exemptions = new_exemptions

    @property
    def newwords(self):
        """Pandas DataFrame of new word entries."""
        return self._newwords

    def _connect_and_populate(self):
        """Connect to db. Create and populate temp tables."""
        logging.debug("Connecting to the database %s", self._db)
        self._connection = sqlite3.connect(self._db)
        self._connection.create_function("REGEXP", 2, regexp)
        self._connection.create_function("REGREPLACE", 3, re.sub)
        self._cursor = self._connection.cursor()
        self._create_temp_tables()
        self._populate_temp_tables()
        if self.newwords is not None:
            self._insert_newwords()
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

    def _insert_newwords(self):
        logging.debug("Inserting lexical additions")
        word_vals, pron_vals = parse_newwords(self.newwords)
        word_insert_stmt = NEWWORD_INSERT.format(
            table=self.word_table,
            columns=NW_WORD_COLS[0],
            vars=NW_WORD_COLS[1]
        )
        pron_insert_stmt = NEWWORD_INSERT.format(
            table=self.pron_table,
            columns=NW_PRON_COLS[0],
            vars=NW_PRON_COLS[1]
        )
        self._cursor.executemany(word_insert_stmt, word_vals)
        self._cursor.executemany(pron_insert_stmt, pron_vals)
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

    def select_pattern_matches(self, rules: list = None):
        """Select all rows that match the patterns in `rules`.

        Parameters
        ----------
        rules: list
            Optional list of rules to run the queries with.
            Default is self.rulesets.

        Returns
        -------
        dict
            {dialect: [(rule_id, db_field1, db_field2, ...), ...], dialect2: [...]}
        """
        if rules is not None:
            self.rulesets = rules
        matching_entries = defaultdict(list)
        logging.info("Fetch words that match the rule patterns")
        for ruleset in self.rulesets:
            for dialect in ruleset.areas:
                for rule in ruleset.rules:
                    pattern = rule.pattern
                    cond_string, cond_values = parse_conditions(
                        rule.constraints,  ruleset.exempt_words
                    )
                    conditions = f" AND {cond_string}" if cond_string else ""
                    query = SELECT_QUERY.format(
                        columns=COL_WORD_PRON_ID,
                        word_table=self.word_table,
                        pron_table=dialect,
                        where_regex=WHERE_REGEXP,
                        where_word_in_stmt=conditions
                    )
                    values = (pattern, *cond_values)
                    logging.debug("Execute SQL Query: %s %s", query, values)
                    word_match = self._cursor.execute(query, values).fetchall()
                    logging.info(
                        "Regex pattern '%s' covers %s matching words for dialect %s",
                        pattern,
                        len(word_match),
                        dialect
                    )
                    matching_entries[dialect].append((rule.id_, word_match))
        return matching_entries

    def update(self, rules: list = None, include_id: bool = False):
        """Update the lexicon database with transformations defined by the `rules`.

        Construct SQL UPDATE queries with the rules and exemptions before
        applying them to the dialect temp tables.

        Parameters
        ----------
        rules: list
            Optional list of rules to run the updates with. Default is self.rulesets.
        include_id: bool
            If include_id is True, the results attribute will include a column
            with the unique_id of the word entry, and the pron_id of the
            transcription.

        Returns
        -------
        dict
            Format: {dialect: [(database_field1, database_field2,...), ...]}
        """
        if rules is not None:
            self.rulesets = rules
        logging.info("Apply rule patterns, update transcriptions")
        for ruleset in self.rulesets:
            exemptions = ruleset.exempt_words
            for dialect in ruleset.areas:
                for rule in ruleset.rules:
                    cond_string, cond_values = parse_conditions(
                        rule.constraints, exemptions
                    )
                    where_word = WHERE_WORD_IN_STMT.format(
                        word_table=self.word_table, conditions=cond_string
                    ) if cond_string else ""
                    query = UPDATE_QUERY.format(
                        dialect=dialect,
                        where_word_in_stmt=where_word
                    )
                    values = (rule.pattern, rule.replacement, *cond_values)
                    logging.debug("Execute SQL Query: %s %s", query, values)
                    self._cursor.execute(query, values)
                    self._connection.commit()
        return self.fetch_dialect_updates(include_id=include_id)

    def fetch_dialect_updates(self, include_id: bool = False) -> dict:
        """Fetch the state of the lexicon db from the dialect temp tables.

        If include_id is True, the results attribute will include a column
        with the unique_id of the word entry, and the pron_id of the
        transcription.

        Returns
        -------
        results: dict
            Dialect names are keys, and the resulting collection of values
            from each field in the database are the values
        """
        results: dict = {dialect: [] for dialect in self.dialects}
        columns_to_fetch = (
            COL_ID_WORD_FEATS_PRON_ID if include_id
            else COL_WORD_POS_FEATS_PRON
        )

        for dialect in self.dialects:
            stmt = SELECT_QUERY.format(
                columns=columns_to_fetch,
                word_table=self.word_table,
                pron_table=dialect,
                where_regex='',
                where_word_in_stmt=''
            )
            logging.debug("Execute SQL Query: %s", stmt)
            results[dialect] = self._cursor.execute(stmt).fetchall()
        return results

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

    def get_tmp_table_state(self):
        """Fetch the state of the temporary tables, including new word
        entries."""
        stmt = SELECT_QUERY.format(
            columns=COL_ID_WORD_FEATS_PRON_ID,
            word_table=self.word_table,
            pron_table=self.pron_table,
            where_regex='',
            where_word_in_stmt=''
        )
        result = self._cursor.execute(stmt).fetchall()
        logging.debug(
            "Fetched %s results from the temp tables with SQL query: \n%s ",
            len(result),
            stmt
        )
        return result

    def get_connection(self):
        """Return the object instance's sqlite3 connection."""
        return self._connection

    def close(self):
        """Close the object instance's sqlite3 connection."""
        self._connection.close()

"""Connect to and update the database containing the pronunciation lexicon."""
from typing import List, Iterable
from collections import defaultdict
import logging
import re
import sqlite3

import pandas as pd

from .dialect_updater import parse_conditions, parse_rulesets, add_placeholders
from .newword_updater import parse_newwords
from .constants import (
    LEXICON_COLUMNS,
    dialect_schema,
    CREATE_PRON_TABLE_STMT,
    CREATE_WORD_TABLE_STMT,
    INSERT_STMT,
    UPDATE_QUERY,
    SELECT_QUERY,
    WHERE_REGEXP,
    NEWWORD_INSERT,
    NW_WORD_COLS,
    NW_PRON_COLS,
    COL_WORDFORM,
    COL_pUID,
    COL_PRONID,
    COL_PRON,
    COL_UID,
    COL_FEATS,
    COL_POS,
    COL_INFO,
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
        self._rulesets = parse_rulesets(new_rulesets, self.exemptions)

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

    def _run_selection(self, query, values) -> Iterable:
        logging.debug("Execute SQL Query: %s %s", query, values)
        return self._cursor.execute(query, values).fetchall()

    def _run_update(self, query, values):
        logging.debug("Execute SQL Query: %s %s", query, values)
        try:
            self._cursor.execute(query, values)
            self._connection.commit()
        except sqlite3.OperationalError:
            logging.error("Skipping update. Couldn't run query: %s", query)

    def select_pattern_matches(self, rulesets: List):
        """Select all rows that match the patterns in `rulesets`.

        Parameters
        ----------
        rulesets: list
            List of RuleSet objects to run the queries with.

        Returns
        -------
        dict
            {dialect: [(rule_id, db_field1, db_field2, ...), ...], dialect2: [...]}
        """
        matching_entries = defaultdict(list)
        logging.info("Fetch words that match the rule patterns")
        for ruleset in rulesets:
            for dialect in ruleset.areas:
                logging.info("Matching words for dialect %s", dialect)
                for rule in ruleset.rules:
                    query, values = self._construct_select_query(
                        dialect, rule.pattern, rule.constraints, ruleset.exempt_words)
                    word_match = self._run_selection(query, values)
                    logging.info(
                        "%s matching words for rule %s ",
                        len(word_match),
                        rule.id_
                    )
                    # yield dialect, rule.id_, word_match
                    matching_entries[dialect].append((rule.id_, word_match))
        return matching_entries

    def select_updates(self, rulesets: Iterable, rule_ids: List[str] = None):
        """Update and select the updated db rows.

        If rule_ids are given, only the updates specified by those rules will be selected.

        Parameters
        ----------
        rulesets: List of RuleSet objects
        rule_ids: List of strings, either ruleset.rules[i].id_ or ruleset.name

        Yields
        ------
        pandas.DataFrame with the selected words and transcriptions before and after updates.
        """
        def rule_iterator():
            for ruleset in rulesets:
                for dialect in ruleset.areas:
                    for rule in ruleset.rules:
                        is_tracked = (ruleset.name in rule_ids) or (rule.id_ in rule_ids)
                        yield rule, ruleset.exempt_words, dialect, is_tracked

        for rule_info in rule_iterator():
            result = self._track_changes_(*rule_info)
            if result is None or result.empty:
                continue
            yield result

    def _track_changes_(self, rule, exemptions, dialect, is_tracked_rule):
        """Apply subfunctions to track changes in specific tables for specific rules."""

        def pre_select_rows():
            """Retrieve the rows that match the rules before updates."""
            select_q, select_v = self._construct_select_query_pre_update(
                LEXICON_COLUMNS, self.word_table, dialect, rule.pattern, rule.constraints, exemptions)
            preupdate_match = self._run_selection(select_q, select_v)
            return pd.DataFrame(preupdate_match, columns=LEXICON_COLUMNS)

        def update_rows():
            """Apply the update rule."""
            update_q, update_v = self._construct_update_query_restricted(
                dialect, rule.pattern, rule.replacement, rule.constraints, exemptions)
            self._run_update(update_q, update_v)

        def post_update_select_rows(pre_update_df):
            """Retrieve new transcriptions from the rows that were updated."""
            pron_ids = pre_update_df[COL_PRONID].to_list()
            try:
                select_q, select_v = self._construct_select_query_post_update(
                    ",".join([COL_PRON, COL_PRONID]), dialect, COL_PRONID, pron_ids)
                postupdate_match = self._run_selection(select_q, select_v)
                updated_df = pd.DataFrame(postupdate_match, columns=["new_transcription",
                                                                     COL_PRONID])

                comparison_df = pre_update_df.merge(updated_df, how='inner', on=[COL_PRONID])
                # track data transformation metadata
                comparison_df.loc[:, "rule_id"] = rule.id_  # definition of update
                comparison_df.loc[:, "dialect"] = dialect  # affected database table
                return comparison_df
            except Exception as e:
                logging.error(e)

        if is_tracked_rule:
            logging.info("Track rule changes for %s", rule.id_)
            match_df = pre_select_rows()
            logging.info("%s rows in %s", len(match_df.index), dialect)
            update_rows()
            return post_update_select_rows(match_df)
        else:
            logging.info("Apply rule changes for %s in %s", rule.id_, dialect)
            update_rows()

    def _construct_select_query(self, dialect, pattern, constraints, exempt_words):
        conditions, cond_values = parse_conditions(constraints, exempt_words, prefix="AND")
        query = SELECT_QUERY.format(
            columns=LEXICON_COLUMNS,
            word_table=self.word_table,
            pron_table=dialect,
            where_regex=WHERE_REGEXP,
            where_word_in_stmt=conditions
        )
        values = (pattern, *cond_values)
        return query, values

    def _construct_select_query_post_update(self, column, table, id_column, id_list):
        query = (
            f"SELECT {column} FROM {table} p WHERE {id_column} IN "
            f"({add_placeholders(id_list)});"
        )
        values = tuple(id_list)
        return query, values

    def _construct_select_query_pre_update(self, columns, word_table, pron_table,
                                           pattern, constraints,
                                           exemptions):
        condition_str, condition_vals = parse_conditions(constraints, exemptions, prefix="AND")
        query = (
            f"SELECT {', '.join(columns)} "
            f"FROM {word_table} w "
            f"LEFT JOIN {pron_table} p "
            "ON p.unique_id = w.unique_id "
            f"WHERE REGEXP(?, p.nofabet) {condition_str};"
        )
        values = (pattern, *condition_vals)
        return query, values

    def _construct_update_query_simple(self, dialect: str, pattern: str, replacement: str):
        query = UPDATE_QUERY.format(dialect=dialect, where_word_in_stmt='')
        values = (pattern, replacement)
        return query, values

    def _construct_update_query_uids(self, dialect: str, pattern: str, replacement: str,
                                     unique_ids: List[str]):
        condition = f"WHERE unique_id IN ({add_placeholders(unique_ids)})"
        query = UPDATE_QUERY.format(dialect=dialect, where_word_in_stmt=condition)
        values = (pattern, replacement, *unique_ids)
        return query, values

    def _construct_update_query_restricted(self, dialect: str, pattern: str, replacement: str,
                                           constraints: list, exemptions: list):
        condition_str, cond_values = parse_conditions(constraints, exemptions, "WHERE")
        condition = (
            f"WHERE unique_id IN (SELECT unique_id FROM {self.word_table} w "
            f" {condition_str})"
        )
        query = UPDATE_QUERY.format(dialect=dialect, where_word_in_stmt=condition)
        values = (pattern, replacement, *cond_values)
        return query, values

    def update(self, rulesets: Iterable, rule_ids: List[str] = None):
        if rule_ids is None:
            rule_ids = []
        for rule in rulesets:
            if rule.dialect not in self.dialects:
                continue
            if (rule.id_ in rule_ids) or (rule.ruleset in rule_ids):
                yield self.track_updates(rule)
            else:
                self.update_rows(rule)

    def track_updates(self, rule):
        match_df = self._select_rows_from_rule(rule)
        logging.info("Rule %s matches %s rows in %s", rule.id_,len(match_df.index), rule.dialect)
        self.update_rows(rule)
        updated_df = self._select_rows_from_ids(rule, match_df)
        return self._merge_comparison_dfs(rule, match_df, updated_df)

    def _select_rows_from_rule(self, rule):
        """Retrieve the rows that match the rules before updates."""
        condition_str, condition_values = parse_conditions(rule.constraints, rule.exemptions, prefix="AND")
        query = (
            f"SELECT {COL_UID},{COL_PRONID},{COL_WORDFORM},{COL_PRON} FROM words_tmp w "
            f"LEFT JOIN {rule.dialect} p ON p.unique_id = w.unique_id "
            f"WHERE REGEXP(?, p.nofabet) {condition_str};"
        )
        values = (rule.pattern, *condition_values)
        return self._get_data(query, values=values)

    def update_rows(self, rule):
        """Apply the update rule."""
        logging.debug("Update with rule ID: %s", rule.id_)
        condition_str, condition_values = parse_conditions(rule.constraints, rule.exemptions, prefix="WHERE")
        query = (
            f"UPDATE {rule.dialect} "
            f"SET nofabet=REGREPLACE(?,?,nofabet) "
            f"WHERE unique_id IN "
            f"(SELECT unique_id FROM {self.word_table} w {condition_str})"
            f";")

        values = (rule.pattern, rule.replacement, *condition_values)
        self._run_update(query, values)

    def _select_rows_from_ids(self, rule, row_df):
        """Retrieve new transcriptions from the rows that were updated."""
        pron_ids = tuple(row_df["pron_id"])
        query = (
            f"SELECT {COL_PRON},{COL_PRONID} FROM {rule.dialect} p WHERE p.pron_id IN "
            f"({add_placeholders(pron_ids)});"
        )
        return self._get_data(query, values=pron_ids)

    def _merge_comparison_dfs(self, rule, pre_update_df, post_update_df ):
        comparison_df = pre_update_df.merge(post_update_df, how='inner', on=["pron_id"])
        comparison_df.loc[:, "rule_id"] = rule.id_
        comparison_df.loc[:, "dialect"] = rule.dialect
        comparison_df = comparison_df.rename(columns={
            "nofabet_x": "transcription",
            "nofabet_y": "new_transcription"})
        return comparison_df


    def update_old(self, rulesets: list, include_id: bool = False):
        """Update the lexicon database with transformations defined by the `rules`.

        Construct SQL UPDATE queries with the rules and exemptions before
        applying them to the dialect temp tables.

        Parameters
        ----------
        rulesets: list
            List of rules to run the updates with.
        include_id: bool
            If include_id is True, the results attribute will include a column
            with the unique_id of the word entry, and the pron_id of the
            transcription.

        Returns
        -------
        dict
            Format: {dialect: [(database_field1, database_field2,...), ...]}
        """
        logging.info("Apply rule patterns, update transcriptions")
        for ruleset in rulesets:
            for dialect in ruleset.areas:
                for rule in ruleset.rules:
                    query, values = self._construct_update_query_restricted(
                       dialect, rule.pattern, rule.replacement,rule.constraints, ruleset.exempt_words)
                    self._run_update(query, values)
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

        for dialect in self.dialects:
            stmt = SELECT_QUERY.format(
                columns=LEXICON_COLUMNS,
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
                columns=LEXICON_COLUMNS,
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
            columns=LEXICON_COLUMNS,
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


    def get_dialect_data(self, dialect_table) -> pd.DataFrame:
        """Fetch data from a dialect temp table in the database.

        Parameters
        ----------
        dialect_table: str
            Name of dialect area to print the lexicon for.
        """
        query = (
            f"SELECT {LEXICON_COLUMNS} "
            f"FROM {self.word_table} w "
            f"LEFT JOIN {dialect_table} p "
            f"ON p.unique_id = w.unique_id;"
        )
        return self._get_data(query)

    def get_original_data(self):
        """Select the original state of the lexicon."""
        query = f"SELECT {LEXICON_COLUMNS} FROM words w LEFT JOIN base p ON p.unique_id = w.unique_id ;"
        return self._get_data(query)

    def get_newwords(self):
        """Select the new word entries."""
        query = (
            f"SELECT {LEXICON_COLUMNS} "
            f"FROM {self.word_table} w "
            f"LEFT JOIN {self.pron_table} p "
            f"ON p.unique_id = w.unique_id "
            f"WHERE REGEXP('NB\\d+', p.unique_id);"
        )
        return self._get_data(query)

    def _get_data(self, query, values=None):
        """Return a dataframe with the select query response."""
        #return self._cursor.execute(query).fetchall()
        if values is None:
            return pd.read_sql_query(query, self._connection)
        else:
            return pd.read_sql_query(query, self._connection, params=values)

    def get_connection(self):
        """Return the object instance's sqlite3 connection."""
        return self._connection

    def close(self):
        """Close the object instance's sqlite3 connection."""
        self._connection.close()

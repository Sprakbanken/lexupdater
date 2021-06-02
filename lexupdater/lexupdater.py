#!/usr/bin/env python
# coding=utf-8

"""Transcription updates for a pronunciation lexicon in sqlite3 db format."""

import datetime
import logging
import pprint
from typing import Iterable

from .config import (
    WORD_TABLE,
    DATABASE,
    RULES,
    EXEMPTIONS,
    OUTPUT_DIR
)
from .db_handler import DatabaseUpdater


def get_base(connection):
    """Select the state of the lexicon before the updates.

    Parameters
    ----------
    connection: sqlite3.connect
        A connection to the open sqlite database

    Returns
    -------
    result: list
        The full contents of the base lexicon
    """
    stmt = """SELECT w.word_id, w.wordform, w.pos, w.feats, w.source,
            w.decomp_ort, w.decomp_pos, w.garbage, w.domain, w.abbr,
            w.set_name, w.style_status, w.inflector_role, w.inflector_rule,
            w.morph_label, w.compounder_code, w.update_info, p.pron_id,
            p.nofabet, p.certainty FROM words w LEFT JOIN base p ON
            p.word_id = w.word_id;"""
    cursor = connection.cursor()
    result = cursor.execute(stmt).fetchall()
    logging.debug(
        "Fetched %s results from the base lexicon with SQL query: \n%s ",
        len(result), stmt)
    return result


def write_lexicon(output_file: str, data: Iterable):
    """Write a simple txt file with the results of the SQL queries.

    Parameters
    ----------
    output_file: str
        Name of the file to write data to
    data: Iterable[dict]
        A collection of dictionaries,
        where the 1st, 2nd, 3rd and 2nd to last elements are saved to disk
    """
    logging.info("Writing lexicon data to %s", output_file)
    with open(output_file, "w") as outfile:
        for item in data:
            outfile.write(f"{item[1]}\t{item[2]}\t{item[3]}\t{item[-2]}\n")


def main(user_dialects, write_base, match_words):
    """Apply the replacement rules from the config on the base lexicon.

    The variable base contains the original state of the lexicon.
    exp contains the modified lexicon based on the rules and
    exemptions specified in the config file. Note that all modifications
    in the backend db target temp tables, so the db isn"t modified.

    The modifications to the lexicon are written to new, dialect-specific
    files.

    Parameters
    ----------
    user_dialects: list
        List of dialects to write updated lexicon .txt-files for
    write_base: bool
        If True, write the base lexicon as a .txt-file
    match_words: bool
        If True, only fetch a list of the matching
    """
    begin_time = datetime.datetime.now()
    logging.debug("Started lexupdater process at %s", begin_time.isoformat())

    update_obj = DatabaseUpdater(
        DATABASE, RULES, user_dialects, WORD_TABLE, exemptions=EXEMPTIONS
    )
    connection = update_obj.get_connection()
    if match_words:
        logging.info("LEXUPDATER: Only print words matching the rule patterns")
        update_obj.select_words_matching_rules()
        for dialect in user_dialects:
            logging.info("--- Dialect: %s ---", dialect)
            pprint.pprint(update_obj.results[dialect])
    else:
        logging.info(
            "LEXUPDATER: Apply rules and update lexicon transcriptions"
        )
        update_obj.update()
        for dialect in user_dialects:
            output_filename = OUTPUT_DIR / f"{dialect}.txt"
            write_lexicon(output_filename, update_obj.results[dialect])
    update_obj.close_connection()

    # Calculating execution time
    update_end_time = datetime.datetime.now()
    update_time = update_end_time - begin_time
    logging.debug("Database updated. Time: %s", update_time)

    if write_base:
        write_lexicon(OUTPUT_DIR / "base.txt", get_base(connection))

        # For calculating execution time
        file_gen_end_time = datetime.datetime.now()
        file_gen_time = file_gen_end_time - update_end_time
        logging.debug("Files generated. Time: %s", file_gen_time)

#!/usr/bin/env python
# coding=utf-8

"""Transcription updates for a pronunciation lexicon in sqlite3 db format."""

import csv
import datetime
import logging
from runpy import run_path
from typing import Iterable

from config import (
    WORD_TABLE,
    DATABASE,
    RULES_FILE,
    EXEMPTIONS_FILE,
    OUTPUT_DIR
)
from .db_handler import DatabaseUpdater


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
    with open(OUTPUT_DIR / output_file, 'w', newline='') as csvfile:
        out_writer = csv.writer(csvfile, delimiter='\t')
        for item in data:
            out_writer.writerow(item)


def write_match_results(output_file, data):
    """Write a simple txt file with the results of the SQL queries.

    Parameters
    ----------
    output_file: str
        Name of the file to write data to
    data: Iterable[tuple]
        A collection of tuples, where the first element is the rule pattern,
        the second is the collection of lexicon rows
        that match the rule pattern
    """
    logging.info("Writing words that match rule patterns to %s", output_file)
    with open(OUTPUT_DIR / output_file, 'w', newline='') as csvfile:
        out_writer = csv.writer(csvfile, delimiter='\t')
        for pattern, words in data:
            for item in words:
                out_writer.writerow([pattern] + list(item))


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
        If True, only fetch a list of words that match the rule patterns
    """
    begin_time = datetime.datetime.now()
    logging.debug("Started lexupdater process at %s", begin_time.isoformat())

    rules = run_path(RULES_FILE).get("ruleset_list")
    exemptions = run_path(EXEMPTIONS_FILE).get("exemptions_list")

    update_obj = DatabaseUpdater(
        DATABASE, rules, user_dialects, WORD_TABLE, exemptions=exemptions
    )
    if write_base:
        base = update_obj.get_base()
    if match_words:
        logging.info("LEXUPDATER: Fetch words that match the rule patterns")
        update_obj.select_words_matching_rules()
    else:
        logging.info("LEXUPDATER: Apply rule patterns, update transcriptions")
        update_obj.update()
    update_obj.close_connection()

    # Calculating execution time
    update_end_time = datetime.datetime.now()
    update_time = update_end_time - begin_time
    logging.debug("Database closed. Time: %s", update_time)

    if write_base:
        write_lexicon("base.txt", base)

    for dialect in user_dialects:
        results = update_obj.results[dialect]
        if not results:
            continue
        if match_words:
            write_match_results(f"words_matching_rules_for_{dialect}.txt", results)
        else:
            write_lexicon(f"updated_lexicon_{dialect}.txt", results)

    # For calculating execution time
    file_gen_end_time = datetime.datetime.now()
    file_gen_time = file_gen_end_time - update_end_time
    logging.debug("Files generated. Time: %s", file_gen_time)
    logging.info("Done.")

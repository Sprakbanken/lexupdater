#!/usr/bin/env python
# coding=utf-8

"""Transcription updates for a pronunciation lexicon in sqlite3 db format."""

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
        If True, only fetch a list of words that match the rule patterns
    """
    begin_time = datetime.datetime.now()
    logging.debug("Started lexupdater process at %s", begin_time.isoformat())

    rules = run_path(RULES_FILE).get("ruleset_list")
    exemptions = run_path(EXEMPTIONS_FILE).get("exemptions_list")

    update_obj = DatabaseUpdater(
        DATABASE, rules, user_dialects, WORD_TABLE, exemptions=exemptions
    )
    connection = update_obj.get_connection()
    if match_words:
        logging.info("LEXUPDATER: Only print words matching the rule patterns")
        update_obj.select_words_matching_rules()
        for dialect in user_dialects:
            matching_words = update_obj.results[dialect]
            if not matching_words:
                continue
            output_file = OUTPUT_DIR / f"words_matching_rules_for_{dialect}.txt"
            logging.info(
                "Writing words that match rule patterns to %s", output_file)
            with open(output_file, "w") as outfile:
                for pattern, words in matching_words:
                    logging.info(
                        "Regex pattern '%s' covers %s matching words ",
                        pattern,
                        len(words)
                    )
                    for item in words:
                        outfile.write(",".join([pattern] + list(item)) + "\n")
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
    logging.info("Done.")

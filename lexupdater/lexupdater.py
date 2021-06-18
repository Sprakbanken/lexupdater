"""Transcription updates for a pronunciation lexicon in sqlite3 db format."""

import argparse
import csv
import datetime
import logging
from typing import Iterable, Tuple

import click

from .constants import (
    WORD_TABLE,
    DATABASE,
    RULES,
    EXEMPTIONS,
    OUTPUT_DIR,
    DIALECTS
)
from .db_handler import DatabaseUpdater
from .utils import write_lexicon, flatten_match_results, load_data, \
    load_module_from_path


@click.command(context_settings={"help_option_names": ['-h', '--help']})
@click.option(
    "-d",
    "--dialects",
    type=str,
    #nargs="+",
    multiple=True,
    default=DIALECTS,
    show_default=True,
    help="Apply replacement rules on one or more specified dialects.",
)
@click.option(
    "-b",
    "--write_base",
    is_flag=True,
    default=False,
    help="Write a lexicon file with the state of the lexicon prior to updates."
)
@click.option(
    "-m",
    "--match_words",
    is_flag=True,
    default=False,
    help=(
        "Print list of the words that will be affected by update rules "
        "for the given dialects"
    )
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Print logging messages at the debugging level."
)
@click.option(
    "-l",
    "--log_file",
    type=str,
    nargs=1,
    help="Write all logging messages to log_file instead of the terminal."
)
def main(**kwargs):
    """Apply the replacement rules from the config on the base lexicon.

    The variable base contains the original state of the lexicon.
    exp contains the modified lexicon based on the rules and
    exemptions specified in the config file. Note that all modifications
    in the backend db target temp tables, so the db isn"t modified.

    The modifications to the lexicon are written to new, dialect-specific
    files.
    """
    # Parse arguments
    user_dialects = list(kwargs.get("dialects"))
    write_base = kwargs.get("write_base")
    match_words = kwargs.get("match_words")
    log_file = kwargs.get("log_file")
    verbose = kwargs.get("verbose")

    # Set up logging config
    logging.basicConfig(
        filename=(OUTPUT_DIR / log_file) if log_file else None,
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s | %(levelname)s | %(module)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M')

    # Log starting time
    begin_time = datetime.datetime.now()
    logging.debug("Started lexupdater process at %s", begin_time.isoformat())

    # Initiate the database connection
    update_obj = DatabaseUpdater(
        DATABASE, RULES, user_dialects, WORD_TABLE, exemptions=EXEMPTIONS
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
            flat_matches = flatten_match_results(results)
            out_file = output_dir / f"words_matching_rules_{dialect}.txt"
            write_lexicon(out_file, flat_matches)
        else:
            out_file = output_dir / f"updated_lexicon_{dialect}.txt"
            write_lexicon(out_file, results)

    # For calculating execution time
    file_gen_end_time = datetime.datetime.now()
    file_gen_time = file_gen_end_time - update_end_time
    logging.debug("Files generated. Time: %s", file_gen_time)
    logging.info("Done.")

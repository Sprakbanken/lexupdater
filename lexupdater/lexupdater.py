"""Transcription updates for a pronunciation lexicon in sqlite3 db format."""

import argparse
import csv
import datetime
import logging
from typing import Iterable

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
    logging.info("Write lexicon data to %s", output_file)
    with open(OUTPUT_DIR / output_file, 'w', newline='') as csvfile:
        out_writer = csv.writer(csvfile, delimiter='\t')
        for item in data:
            out_writer.writerow(item)


def flatten_match_results(data):
    """Flatten a nested list of rule pattern matches.

    Parameters
    ----------
    data: Iterable[tuple]
        A collection of tuples, where the first element is the rule pattern,
        the second is the collection of lexicon rows
        that match the rule pattern
    """
    for pattern, words in data:
        for item in words:
            yield [pattern] + list(item)




@click.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")


@click.option(
    "-d",
    "--dialects",
    action="store",
    type=str,
    nargs="+",
    default=DIALECTS,
    help="Apply replacement rules on one or more specified dialects.",
)
@click.option(
    "--write_base",
    "-b",
    action="store_true",
    help=(
        "Generate a base lexicon file, containing the state of the lexicon "
        "prior to updates."
    )
)
@click.option(
    "--match_words",
    "-m",
    action="store_true",
    help=(
        "Print list of the words that will be affected by update rules "
        "for the given dialects"
    )
)
@click.option(
    "--verbose",
    "-v",
    action="store_true",
    help=(
        "Print logging messages at the debugging level. "
        "See python documentation on logging for more info."
    )
)
@click.option(
    "--log_file",
    "-l",
    action="store",
    type=str,
    nargs="?",
    help="Save all logging messages to the given file. ",
)
def main():
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

    # Argument parser
    parser = argparse.ArgumentParser()

"""    parser.add_argument(
        "--dialects",
        "-d",
        action="store",
        type=str,
        nargs="+",
        default=DIALECTS,
        help="Apply replacement rules on one or more specified dialects.",
    )
    parser.add_argument(
        "--write_base",
        "-b",
        action="store_true",
        help=(
            "Generate a base lexicon file, containing the state of the lexicon "
            "prior to updates."
        )
    )
    parser.add_argument(
        "--match_words",
        "-m",
        action="store_true",
        help=(
            "Print list of the words that will be affected by update rules "
            "for the given dialects"
        )
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help=(
            "Print logging messages at the debugging level. "
            "See python documentation on logging for more info."
        )
    )
    parser.add_argument(
        "--log_file",
        "-l",
        action="store",
        type=str,
        nargs="?",
        help="Save all logging messages to the given file. ",
    )"""
    args = parser.parse_args()

    if args.verbose:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    logging.basicConfig(
        filename=(OUTPUT_DIR / args.log_file) if args.log_file else None,
        level=logging_level,
        format='%(asctime)s | %(levelname)s | %(module)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M')

    begin_time = datetime.datetime.now()
    logging.debug("Started lexupdater process at %s", begin_time.isoformat())

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
            write_lexicon(f"words_matching_rules_{dialect}.txt", flat_matches)
        else:
            write_lexicon(f"updated_lexicon_{dialect}.txt", results)

    # For calculating execution time
    file_gen_end_time = datetime.datetime.now()
    file_gen_time = file_gen_end_time - update_end_time
    logging.debug("Files generated. Time: %s", file_gen_time)
    logging.info("Done.")

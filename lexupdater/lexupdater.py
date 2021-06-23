"""Transcription updates for a pronunciation lexicon in sqlite3 db format."""

import datetime
import logging
from pathlib import Path

import click

from .db_handler import DatabaseUpdater
from .utils import (
    write_lexicon,
    flatten_match_results,
    load_data,
    load_module_from_path
)


@click.command(context_settings={"help_option_names": ['-h', '--help']})
@click.option(
    "-b",
    "--write-base",
    is_flag=True,
    help="Write a lexicon file with the state of the lexicon prior to updates."
)
@click.option(
    "-m",
    "--match-words",
    is_flag=True,
    help=(
        "Write file with the words that will be affected by update rules "
        "for the given dialects."
    )
)
@click.option(
    "-d",
    "--dialects",
    type=str,
    multiple=True,
    help="Apply replacement rules on one or more specified dialects.",
)
@click.option(
    "-r",
    "--rules-file",
    type=str,
    nargs=1,
    help="Apply replacement rules from the given file path.",
)
@click.option(
    "-r",
    "--exemptions-file",
    type=str,
    nargs=1,
    help="Apply exemptions from the given file path to the rules.",
)
@click.option(
    "--db",
    type=str,
    nargs=1,
    help="The path to the lexicon database.",
)
@click.option(
    "-o",
    "--output-dir",
    type=str,
    nargs=1,
    help="The directory path that files are written to.",
)
@click.option(
    "-l",
    "--log-file",
    type=str,
    nargs=1,
    help="Write all logging messages to log_file instead of the terminal."
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Print logging messages at the debugging level."
)
@click.option(
    "-c",
    "--config-file",
    type=str,
    nargs=1,
    default="config.py",
    show_default=True,
    help="Path to config.py file."
)
def main(**kwargs):
    """Apply the dialect update rules on the base lexicon.

    Default file paths to the lexicon database, the replacement rules,
    and their exemptions, as well as the output directory,
    are specified in the config.py file.

    If provided, CLI arguments override the default values from the config.

    Note that all modifications in the backend db target temp tables,
    so the db isn't modified.
    The modifications to the lexicon are written to
    new, dialect-specific files.
    """
    # Load and import config
    config_file = Path(kwargs.get("config_file")).resolve()
    config = load_module_from_path(config_file)

    # Parse input arguments from the command line and config file
    write_base = kwargs.get("write_base")
    match_words = kwargs.get("match_words")
    log_file = kwargs.get("log_file")
    verbose = kwargs.get("verbose")

    def get_arg(cli_arg, conf_value):
        """Prioritize the user input over config values"""
        return conf_value if cli_arg is None or not cli_arg else cli_arg

    database = get_arg(kwargs.get("db"), config.DATABASE)
    output_dir = Path(get_arg(kwargs.get("output_dir"), config.OUTPUT_DIR))
    word_table = config.WORD_TABLE
    user_dialects = get_arg(list(kwargs.get("dialects")), config.DIALECTS)
    rules_file = get_arg(kwargs.get("rules_file"), config.RULES_FILE)
    exemptions_file = get_arg(
        kwargs.get("exemptions_file"), config.EXEMPTIONS_FILE
    )

    # Load arguments into python data structures
    rules = load_data(rules_file)
    exemptions = load_data(exemptions_file)

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Set up logging config
    logging.basicConfig(
        filename=(output_dir / log_file) if log_file else None,
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s | %(levelname)s | %(module)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M')

    # Log starting time
    begin_time = datetime.datetime.now()
    logging.debug("Started lexupdater process at %s", begin_time.isoformat())

    # Initiate the database connection
    update_obj = DatabaseUpdater(
        database,
        rules,
        user_dialects,
        word_table,
        exemptions=exemptions
    )
    # Run lexupdater according to user input
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

    # Write output
    if write_base:
        write_lexicon((output_dir / "base.txt"), base)

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

    # Calculating execution time
    file_gen_end_time = datetime.datetime.now()
    file_gen_time = file_gen_end_time - update_end_time
    logging.debug("Files generated. Time: %s", file_gen_time)
    logging.info("Done.")

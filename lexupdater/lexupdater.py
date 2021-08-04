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
    load_module_from_path,
    load_newwords
)
from .constants import newword_column_names


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
    help="Apply replacement rules from the given file path.",
)
@click.option(
    "-e",
    "--exemptions-file",
    type=str,
    help="Apply exemptions from the given file path to the rules.",
)
@click.option(
    "-n",
    "--newword-files",
    type=str,
    multiple=True,
    help="Paths to csv files with new words to add to the lexicon."
)
@click.option(
    "--db",
    type=str,
    help="The path to the lexicon database.",
)
@click.option(
    "-o",
    "--output-dir",
    type=str,
    help="The directory path that files are written to.",
)
@click.option(
    "-v",
    "--verbose-info",
    is_flag=True,
    help="Print log messages to the console in addition to the logging file."
)
@click.option(
    "-vv",
    "--verbose-debug",
    is_flag=True,
    help="Print detailed log messages at debugging level to the console."
)
@click.option(
    "-c",
    "--config-file",
    type=str,
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
    def get_arg(cli_arg, conf_value):
        """Prioritize the user input over config values"""
        return conf_value if cli_arg is None or not cli_arg else cli_arg

    output_dir = Path(
        get_arg(kwargs.get("output_dir"), config.OUTPUT_DIR)
    ).resolve()  # <-- Should make default linux paths work in Windows
    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            "%(asctime)s | %(levelname)s "
            "| %(module)s-%(funcName)s-%(lineno)04d | %(message)s"),
        datefmt='%Y-%m-%d %H:%M',
        filename=str(output_dir / "log.txt"),
        filemode='a')
    verbose_debug = kwargs.get("verbose_debug")
    log_level = logging.DEBUG if verbose_debug else logging.INFO
    if kwargs.get("verbose_info") or verbose_debug:
        # define a Handler which writes log messages to stderr
        console = logging.StreamHandler()
        console.setLevel(log_level)
        # set a format which is simpler for console use
        formatter = logging.Formatter(
            '%(asctime)-10s | %(levelname)s | %(message)s')
        # tell the handler to use this format
        console.setFormatter(formatter)
        # add the handler to the root logger
        logging.getLogger('').addHandler(console)

    # Boolean flags that decide which operation to perform
    write_base = kwargs.get("write_base")
    match_words = kwargs.get("match_words")

    # Data input files
    database = get_arg(kwargs.get("db"), config.DATABASE)
    user_dialects = get_arg(list(kwargs.get("dialects")), config.DIALECTS)
    rules_file = get_arg(kwargs.get("rules_file"), config.RULES_FILE)
    exemptions_file = get_arg(
        kwargs.get("exemptions_file"), config.EXEMPTIONS_FILE
    )
    newword_files = get_arg(
        list(kwargs.get("newword_files")), config.NEWWORD_FILES
    )

    # Load file contents into python data structures
    rules = load_data(rules_file)
    exemptions = load_data(exemptions_file)
    newwords = load_newwords(newword_files, newword_column_names)

    logging.info(
        "Loading contents of %s, %s, and %s and applying on %s. "
        "Output will be written to %s",
        rules_file,
        exemptions_file,
        newword_files,
        database,
        output_dir
    )

    # Log starting time
    begin_time = datetime.datetime.now()
    logging.info("START")
    print(f"{begin_time} Loading database")

    # Initiate the database connection
    update_obj = DatabaseUpdater(
        database,
        rules,
        user_dialects,
        exemptions=exemptions,
        newwords=newwords
    )
    # Run lexupdater according to user input
    if write_base:
        base = update_obj.get_base()
    if match_words:
        print("Run SELECT queries on the database")
        results = update_obj.select_words_matching_rules()
    else:
        print("Run UPDATE queries on the database")
        results = update_obj.update()
    update_obj.close_connection()

    # Calculating execution time
    end_time = datetime.datetime.now()
    update_time = end_time - begin_time
    logging.info("Database closed. Update time: %s", update_time)

    print("Write output")
    if write_base:
        write_lexicon((output_dir / "base.txt"), base)
    for dialect in user_dialects:
        data = results[dialect]
        if not data:
            continue
        if match_words:
            flat_matches = flatten_match_results(data)
            out_file = output_dir / f"words_matching_rules_{dialect}.txt"
            write_lexicon(out_file, flat_matches)
        else:
            out_file = output_dir / f"updated_lexicon_{dialect}.txt"
            write_lexicon(out_file, data)

    # Calculating execution time
    file_gen_end_time = datetime.datetime.now()
    file_gen_time = file_gen_end_time - end_time
    logging.debug("Files generated. Time: %s", file_gen_time)
    print(file_gen_end_time, "Done.")
    print(f"Output files, including log messages, are in {output_dir}")

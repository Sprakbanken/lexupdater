"""Transcription updates for a pronunciation lexicon in sqlite3 db format."""

import datetime
import json
import logging
from pathlib import Path
from typing import Iterable

import click

from .db_handler import DatabaseUpdater
from .utils import (
    write_lexicon,
    flatten_match_results,
    load_data,
    load_module_from_path,
    load_newwords,
    convert_lex_to_mfa
)
from .constants import newword_column_names


def configure(ctx, param, filename):
    cfg = load_module_from_path(filename).__dict__
    ctx.default_map = {key.lower():value for key, value in cfg.items()}


def split_multiple_args(ctx, param, arg):
    if isinstance(arg, Iterable):
        return [s for string in arg for s in string.split(",")]
    if isinstance(arg, str):
        return arg.split(",")


def configure_logging(ctx, param, verbose):
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            "%(asctime)s | %(levelname)s "
            "| %(module)s-%(funcName)s-%(lineno)04d | %(message)s"),
        datefmt='%Y-%m-%d %H:%M',
        filename=ctx.default_map.get("output_dir",".") + "/log.txt",
        filemode='a')

    def log_level(verbosity: int):
        return (3 - verbosity) * 10 if verbosity in (0, 1, 2) else 10

    if verbose:
        # define a Handler which writes log messages to stderr
        console = logging.StreamHandler()
        console.setLevel(log_level(verbose))
        # set a format which is simpler for console use
        formatter = logging.Formatter(
            '%(asctime)-10s | %(levelname)s | %(message)s')
        # tell the handler to use this format
        console.setFormatter(formatter)
        # add the handler to the root logger
        logging.getLogger('').addHandler(console)

    return verbose

@click.command(context_settings={"help_option_names": ['-h', '--help']})
@click.option(
    '-c', '--config',
    type=click.Path(dir_okay=False),
    default="./config.py",
    callback=configure,
    is_eager=True,
    expose_value=False,
    help='Read config defaults from the specified .py file',
    show_default=True,
)
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
    help="Write file with the words that will be affected by update rules "
         "for the given dialects."
)
@click.option(
    "-l",
    "--mfa-lexicon",
    is_flag=True,
    help="Convert the output lexicon files to a format that is compatible with "
         "the Montreal Forced Aligner algorithm. "
)
@click.option(
    "-s",
    "--spoken",
    "spoken_prob",
    default=1.0,
    help="Probability assigned to spoken dialectal transcriptions in the MFA "
         "dictionary, if --mfa-lexicon is enabled."
)
@click.option(
    "-w",
    "--written",
    "written_prob",
    default=1.0,
    help="Probability assigned to dialectal transcriptions close to written "
         "form in the MFA dictionary, if --mfa-lexicon is enabled."
)
@click.option(
    "-d",
    "--dialects",
    type=str,
    multiple=True,
    callback=split_multiple_args,
    help="Apply replacement rules on one or more specified dialects. "
         "Args must be separated by a simple comma (,) and no white-space.",
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
    "--no-exemptions",
    is_flag=True,
    help="Disable any exemptions."
)
@click.option(
    "-n",
    "--newword-files",
    type=str,
    multiple=True,
    callback=split_multiple_args,
    help="Paths to csv files with new words to add to the lexicon.",
)
@click.option(
    "--no-newwords",
    is_flag=True,
    help="Disable any newword-updates."
)
@click.option(
    "-db",
    "--database",
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
    "--verbose",
    count=True,
    callback=configure_logging,
    help="Print logging messages to the console in addition to the log file. "
         "-v is informative, -vv is detailed (for debugging)."
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
    if kwargs.get("verbose"):
        click.secho(
            f"Script configuration values: \n"
            f"{json.dumps(kwargs, sort_keys=True, indent=4)}", fg="yellow")

    # default POSIX paths should work in Windows
    output_dir = Path(kwargs.get("output_dir")).resolve()

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Boolean flags that decide which operation to perform
    write_base = kwargs.get("write_base")
    match_words = kwargs.get("match_words")
    mfa_lexicon = kwargs.get("mfa_lexicon")
    no_exemptions = kwargs.get("no_exemptions")
    no_newwords = kwargs.get("no_newwords")

    # Data input files
    database = kwargs.get("database")
    user_dialects = kwargs.get("dialects")
    rules_file = kwargs.get("rules_file")
    exemptions_file = kwargs.get("exemptions_file")
    newword_files = kwargs.get("newword_files")

    # Load file contents into python data structures
    rules = load_data(rules_file)
    exemptions = load_data(exemptions_file) if not no_exemptions else None
    newwords = (
        load_newwords(newword_files, newword_column_names)
        if not no_newwords else None
    )

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
    click.echo(f"{begin_time} Loading database")

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
        click.echo("Run SELECT queries on the database")
        results = update_obj.select_words_matching_rules()
    else:
        click.echo("Run UPDATE queries on the database")
        results = update_obj.update()
    update_obj.close_connection()

    # Calculating execution time
    end_time = datetime.datetime.now()
    update_time = end_time - begin_time
    logging.info("Database closed. Update time: %s", update_time)

    click.echo("Write output")
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
    if mfa_lexicon:
        click.echo("Convert lexica to MFA dict format")
        logging.info("Converting lexica for %s to MFA format", user_dialects)
        convert_lex_to_mfa(
            lex_dir=output_dir,
            dialects=user_dialects,
            combine_dialect_forms=True,
            written_prob=kwargs.get("written_prob"),
            spoken_prob=kwargs.get("spoken_prob"),
        )

    # Calculating execution time
    file_gen_end_time = datetime.datetime.now()
    file_gen_time = file_gen_end_time - end_time
    logging.debug("Files generated. Time: %s", file_gen_time)
    click.echo(f"Output files, including log messages, are in {output_dir}")
    click.echo(f"{file_gen_end_time} Done.")

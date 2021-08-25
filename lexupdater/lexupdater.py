"""Transcription updates for a pronunciation lexicon in sqlite3 db format."""

import datetime
import logging
import pathlib
import pprint
from pathlib import Path
from contextlib import closing

import click

from .db_handler import DatabaseUpdater
from .utils import (
    write_lexicon,
    flatten_match_results,
    load_data,
    load_module_from_path,
    load_newwords,
    convert_lex_to_mfa, validate_phonemes
)
from .constants import (
    newword_column_names,
    LEX_PREFIX,
    MATCH_PREFIX,
    NEW_PREFIX
)


def configure(ctx, param, filename):
    """Load default values from config file."""
    cfg = load_module_from_path(filename).__dict__
    ctx.default_map = {key.lower(): value for key, value in cfg.items()}


def ensure_path(ctx, param, path):
    """Make sure directory exists."""
    path.mkdir(exist_ok=True, parents=True)
    return path


def default_from_context(default_name):
    """Let the context be created and set default values.

    Code from stackoverflow:
    https://stackoverflow.com/questions/56042757/can-i-use-a-context-value-as-a-click-option-default
    """
    class OptionDefaultFromContext(click.Option):
        """Overwriting default value of an option object."""
        def get_default(self, ctx, call=False):
            self.default = ctx.obj[default_name]
            return super(OptionDefaultFromContext, self).get_default(ctx)

    return OptionDefaultFromContext


def split_multiple_args(ctx, param, arg):
    """Create a list from an option value where 'multiple=True'. """
    argslist = []
    for value in arg:
        if isinstance(value, str) and "," in value:
            argslist.extend(value.split(","))
        else:
            argslist.append(value)
    return argslist


def configure_logging(ctx, param, verbose):
    """Configure logging level and destination based on user input."""
    output_dir = Path(ctx.default_map.get("output_dir", "."))
    output_dir.mkdir(exist_ok=True, parents=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            "%(asctime)s | %(levelname)s "
            "| %(module)s-%(funcName)s-%(lineno)04d | %(message)s"),
        datefmt='%Y-%m-%d %H:%M',
        filename=output_dir / "log.txt",
        filemode='a')

    def log_level(verbosity: int):
        """Calculate the log level given by the number of -v flags.

        0 = logging.WARNING (30)
        1 = logging.INFO (20)
        2 = logging.DEBUG (10)
        """
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


@click.group(
    context_settings={"help_option_names": ['-h', '--help']},
    invoke_without_command=True,
    chain=True,
)
@click.option(
    '-c', '--config',
    type=click.Path(exists=True, dir_okay=False),
    default="./config.py",
    callback=configure,
    is_eager=True,
    expose_value=False,
    help='Read config defaults from the specified .py file',
    show_default=True,
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
    type=click.Path(resolve_path=True, exists=True, path_type=pathlib.Path),
    help="Apply replacement rules from the given file path.",
    default="rules.py"
)
@click.option(
    "-e",
    "--exemptions-file",
    type=click.Path(resolve_path=True, exists=True, path_type=pathlib.Path),
    help="Apply exemptions from the given file path to the rules.",
    default="exemptions.py"
)
@click.option(
    "--no-exemptions",
    is_flag=True,
    help="Disable any exemptions."
)
@click.option(
    "-p",
    "--valid-phonemes",
    nargs=1,
    type=click.Path(resolve_path=True, exists=True, path_type=pathlib.Path),
    callback=lambda ctx, param, file: file.read_text().split("\n"),
    help="Verify that all phonemes in the lexicon transcriptions are in the "
         "given phoneme inventory file, with one phoneme per line.",
    default="phoneme_inventory.txt"
)
@click.option(
    "-n",
    "--newword-files",
    type=click.Path(resolve_path=True, exists=True, path_type=pathlib.Path),
    multiple=True,
    callback=split_multiple_args,
    help="Paths to csv files with new words to add to the lexicon.",
)
@click.option(
    "-db",
    "--database",
    type=click.Path(resolve_path=True, dir_okay=False, path_type=pathlib.Path),
    help="The path to the lexicon database.",
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(resolve_path=True, file_okay=False, path_type=pathlib.Path),
    help="The directory path that files are written to.",
    callback=ensure_path,
    is_eager=True
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    callback=configure_logging,
    help="Print logging messages to the console in addition to the log file. "
         "-v is informative, -vv is detailed (for debugging)."
)
@click.pass_context
def main(ctx, database, dialects, rules_file, exemptions_file,
         no_exemptions, valid_phonemes, newword_files, output_dir, verbose):
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
    ctx.ensure_object(dict)
    valid_phonemes.remove("")
    ctx.obj.update(ctx.params)
    if verbose:
        click.secho(
            f"Script configuration values: \n"
            f"{pprint.pformat(ctx.params)}", fg="yellow")

    # Log starting time
    logging.info("START")


    if ctx.invoked_subcommand is None:
        rulesets = load_data(rules_file)
        exemptions = load_data(exemptions_file) if not no_exemptions else None
        newwords = load_newwords(newword_files, newword_column_names)

        click.secho('Run full update', fg="cyan")
        click.echo(f"{datetime.datetime.now()} Loading database")
        with closing(
                DatabaseUpdater(
                    database,
                    dialects,
                    rulesets=rulesets,
                    newwords=newwords,
                    exemptions=exemptions)
        ) as db_obj:
            updated_lex = db_obj.update()
        for dialect, data in updated_lex.items():
            validated_transcriptions = validate_phonemes(data, valid_phonemes)
            write_lexicon(output_dir / f"{LEX_PREFIX}_{dialect}.txt", data)
            write_lexicon(
                output_dir / f"invalid_transcriptions_{dialect}.txt",
                validated_transcriptions["invalid"])
        click.secho(f"Database closed. Files written to {output_dir}",
                    fg="green")


@main.command("base")
@click.option(
    "-db",
    "--database",
    type=click.Path(resolve_path=True, dir_okay=False, path_type=pathlib.Path),
    help="The path to the lexicon database.",
    cls=default_from_context('database'),
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(resolve_path=True, file_okay=False, path_type=pathlib.Path),
    help="The directory path that files are written to.",
    cls=default_from_context('output_dir'),
    callback=ensure_path,
)
@click.pass_context
def write_base(ctx, database, output_dir):
    """Export the base lexicon prior to updates."""
    click.secho("Write the base lexicon to file.",
                fg="cyan")
    with closing(
            DatabaseUpdater(
                db=database,
                dialects=list()
            )
    ) as db_obj:
        base = db_obj.get_base()
    write_lexicon((output_dir / "base.txt"), base)


@main.command("match")
@click.option(
    "-db",
    "--database",
    type=click.Path(resolve_path=True, dir_okay=False, path_type=pathlib.Path),
    help="The path to the lexicon database.",
    cls=default_from_context('database'),
)
@click.option(
    "-d",
    "--dialects",
    type=str,
    multiple=True,
    callback=split_multiple_args,
    help="Apply replacement rules on one or more specified dialects. "
         "Args must be separated by a simple comma (,) and no white-space.",
    cls=default_from_context('dialects'),
)
@click.option(
    "-r",
    "--rules-file",
    type=click.Path(resolve_path=True, exists=True, path_type=pathlib.Path),
    help="Apply replacement rules from the given file path.",
    cls=default_from_context('rules_file'),
)
@click.option(
    "-e",
    "--exemptions-file",
    type=click.Path(resolve_path=True, exists=True, path_type=pathlib.Path),
    help="Apply exemptions from the given file path to the rules.",
    cls=default_from_context('exemptions_file'),
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(resolve_path=True, file_okay=False, path_type=pathlib.Path),
    help="The directory path that files are written to.",
    cls=default_from_context('output_dir'),
    callback=ensure_path,
)
@click.pass_context
def match_words(ctx, database, dialects, rules_file, exemptions_file,
                output_dir):
    """Fetch database entries that match the replacement rules."""
    click.secho("Match database entries to dialect update rules",
                fg="cyan")
    rulesets = load_data(rules_file)
    exemptions = load_data(exemptions_file)
    with closing(
            DatabaseUpdater(
                db=database,
                dialects=dialects,
                rulesets=rulesets,
                exemptions=exemptions)
    ) as db_obj:
        matches = db_obj.select_words_matching_rules()
    for dialect, data in matches.items():
        flat_matches = flatten_match_results(data)
        out_file = (output_dir / f"{MATCH_PREFIX}_{dialect}.txt")
        write_lexicon(out_file, flat_matches)


@main.command("update")
@click.option(
    "-db",
    "--database",
    type=click.Path(resolve_path=True, dir_okay=False, path_type=pathlib.Path),
    help="The path to the lexicon database.",
    cls=default_from_context('database'),
)
@click.option(
    "-d",
    "--dialects",
    type=str,
    multiple=True,
    callback=split_multiple_args,
    help="Apply replacement rules on one or more specified dialects. "
         "Args must be separated by a simple comma (,) and no white-space.",
    cls=default_from_context('dialects'),
)
@click.option(
    "-r",
    "--rules-file",
    type=click.Path(resolve_path=True, exists=True, path_type=pathlib.Path),
    help="Apply replacement rules from the given file path.",
    cls=default_from_context('rules_file'),
)
@click.option(
    "-e",
    "--exemptions-file",
    type=click.Path(resolve_path=True, exists=True, path_type=pathlib.Path),
    help="Apply exemptions from the given file path to the rules.",
    cls=default_from_context('exemptions_file'),
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(resolve_path=True, file_okay=False, path_type=pathlib.Path),
    help="The directory path that files are written to.",
    cls=default_from_context('output_dir'),
    callback=ensure_path,
)
@click.option(
    "-p",
    "--check-phonemes",
    is_flag=True,
    help="Verify that all phonemes in the lexicon transcriptions are in the "
         "given phoneme inventory file, with one phoneme per line."
)
@click.pass_context
def update_dialects(
        ctx, database, dialects, rules_file, exemptions_file, output_dir,
        check_phonemes):
    """Update dialect transcriptions with rules."""
    click.secho("Update dialect transcriptions", fg="cyan")
    rulesets = load_data(rules_file)
    exemptions = load_data(exemptions_file)
    with closing(
            DatabaseUpdater(
                db=database,
                dialects=dialects,
                rulesets=rulesets,
                exemptions=exemptions)
    ) as db_obj:
        updated_lex = db_obj.update()
    for dialect, data in updated_lex.items():
        out_file = (output_dir / f"{LEX_PREFIX}_{dialect}.txt")
        write_lexicon(out_file, data)
        if check_phonemes:
            validated = validate_phonemes(data, ctx.obj["valid_phonemes"])
            invalid_transcriptions_file = (
                output_dir / f"invalid_transcriptions_{dialect}.txt")
            write_lexicon(invalid_transcriptions_file, validated["invalid"])
            click.secho(f"{len(validated['invalid'])} invalid transcriptions "
                        f"in {invalid_transcriptions_file}", fg="magenta")


@main.command("insert")
@click.option(
    "-db",
    "--database",
    type=click.Path(resolve_path=True, dir_okay=False, path_type=pathlib.Path),
    help="The path to the lexicon database.",
    cls=default_from_context('database'),
)
@click.option(
    "-d",
    "--dialects",
    type=str,
    multiple=True,
    callback=split_multiple_args,
    help="Apply replacement rules on one or more specified dialects. "
         "Args must be separated by a simple comma (,) and no white-space.",
    cls=default_from_context('dialects'),
)
@click.option(
    "-n",
    "--newword-files",
    type=click.Path(resolve_path=True, exists=True, path_type=pathlib.Path),
    multiple=True,
    callback=split_multiple_args,
    help="Paths to csv files with new words to add to the lexicon.",
    cls=default_from_context('newword_files'),
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(resolve_path=True, file_okay=False, path_type=pathlib.Path),
    help="The directory path that files are written to.",
    cls=default_from_context('output_dir'),
    callback=ensure_path,
)
@click.pass_context
def insert_newwords(ctx, database, dialects, newword_files, output_dir):
    """Insert new word entries to the lexicon."""
    click.secho("Add new words to database", fg="cyan")
    newwords = load_newwords(newword_files, newword_column_names)
    with closing(
            DatabaseUpdater(
                db=database,
                dialects=dialects,
                newwords=newwords)
    ) as db_obj:
        # Oppdater leksika med lexupdater
        lex_with_newwords = db_obj.get_tmp_table_state()
    write_lexicon((output_dir / f"{NEW_PREFIX}.txt"), lex_with_newwords)


@main.command("convert")
@click.option(
    "-l",
    "--lexicon-dir",
    type=click.Path(resolve_path=True, file_okay=False, path_type=pathlib.Path),
    cls=default_from_context('output_dir'),
    callback=ensure_path,
    help="Directory where updated lexicon .txt files are located, and that "
         "converted .dict files will be written to."
)
@click.option(
    "-co",
    "--combine",
    is_flag=True,
    help="Merge dialect_spoken and dialect_written transcriptions in "
         "the MFA dictionary, and weight the pronunciations with probabilities."
)
@click.option(
    "-s",
    "--spoken",
    "spoken_prob",
    default=1.0,
    help="Probability assigned to spoken dialectal transcriptions in the MFA "
         "dictionary, if --combine is enabled."
)
@click.option(
    "-w",
    "--written",
    "written_prob",
    default=1.0,
    help="Probability assigned to dialectal transcriptions close to written "
         "form in the MFA dictionary, if --combine is enabled."
)
@click.pass_context
def convert_format(ctx, lexicon_dir, combine, spoken_prob, written_prob):
    """Convert lexicon formats to comply with MFA."""
    click.secho("Convert lexica to MFA dict format", fg="cyan")
    convert_lex_to_mfa(
        lex_dir=lexicon_dir,
        combine_dialect_forms=combine,
        written_prob=written_prob,
        spoken_prob=spoken_prob,
    )

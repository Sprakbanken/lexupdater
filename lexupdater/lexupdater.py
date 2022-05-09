"""Transcription updates for a pronunciation lexicon in sqlite3 db format."""

import logging
import pathlib
import pprint
from contextlib import closing
from datetime import datetime
from pathlib import Path

import click
import pandas as pd

from .constants import (
    newword_column_names,
    LEX_PREFIX,
    MATCH_PREFIX,
    NEW_PREFIX,
    dialect_schema,
    COL_WORDFORM
)
from .db_handler import DatabaseUpdater
from .rule_objects import save_rules_and_exemptions, construct_rulesets, RuleSet
from .utils import (
    write_lexicon,
    flatten_match_results,
    load_data,
    load_module_from_path,
    load_newwords,
    convert_lex_to_mfa,
    validate_phonemes,
    write_lex_per_dialect,
    compare_transcriptions,
    ensure_path_exists
)


def configure(ctx, param, filename):
    """Load default values from config file."""
    cfg = load_module_from_path(filename).__dict__
    ctx.default_map = {key.lower(): value for key, value in cfg.items()}


def ensure_path(ctx, param, path):
    """Create dir paths given by command line."""
    return ensure_path_exists(path)


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
    new, temp-table-specific files.
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

    if ctx.invoked_subcommand is None:  # else the subcommand is called by default
        rulesets = load_data(rules_file)
        exemptions = load_data(exemptions_file) if not no_exemptions else None
        rulesets = construct_rulesets(rulesets, exemptions, use_dialects=dialects)
        newwords = load_newwords(newword_files, newword_column_names)

        click.secho('Run full update', fg="cyan")
        click.echo(f"{datetime.now()} Loading database")
        with closing(
                DatabaseUpdater(
                    database,
                    temp_tables=dialects,
                    newwords=newwords)
        ) as db_obj:
            updated_lex = db_obj.update(rulesets)
        for dialect, data in updated_lex.items():
            invalid_transcriptions = validate_phonemes(
                data, valid_phonemes, return_transcriptions="invalid")
            write_lexicon(output_dir / f"{LEX_PREFIX}_{dialect}.txt", data)
            write_lexicon(
                output_dir / f"invalid_transcriptions_{dialect}.txt",
                invalid_transcriptions)
        click.secho(f"Database closed. Files written to {output_dir}",
                    fg="green")


@main.command("base")
@click.pass_context
def write_base(ctx):
    """Export the base lexicon prior to updates."""
    click.secho("Write the base lexicon to file.",
                fg="cyan")
    with closing(
            DatabaseUpdater(
                db=ctx.obj.get("database"),
                temp_tables=[]
            )
    ) as db_obj:
        base = db_obj.get_base()
    write_lexicon((ctx.obj.get("output_dir") / "base.txt"), base)


@main.command("match")
@click.pass_context
def match_words(ctx):
    """Fetch database entries that match the replacement rules."""
    click.secho("Match database entries to dialect update rules",
                fg="cyan")
    # Preprocess input data
    rules = load_data(ctx.obj.get("rules_file"))
    exemptions = load_data(ctx.obj.get("exemptions_file"))
    dialects = ctx.obj.get("dialects")
    rulesets = construct_rulesets(rules, exemptions, dialects)
    output_dir = ctx.obj.get("output_dir")

    with closing(
            DatabaseUpdater(
                db=ctx.obj.get("database"),
                temp_tables=dialects,
            )
    ) as db_obj:
        matches = db_obj.select_pattern_matches(rulesets)
    write_lex_per_dialect(
        matches, output_dir, MATCH_PREFIX, flatten_match_results)


@main.command("update")
@click.option(
    "-p",
    "--check-phonemes",
    is_flag=True,
    help="Verify that all phonemes in the lexicon transcriptions are in the "
         "given phoneme inventory file, with one phoneme per line."
)
@click.pass_context
def update_dialects(
        ctx, check_phonemes):
    """Update dialect transcriptions with rules."""
    click.secho("Update dialect transcriptions", fg="cyan")
    rules = load_data(ctx.obj.get("rules_file"))
    exemptions = load_data(ctx.obj.get("exemptions_file"))
    dialects = ctx.obj.get("dialects")
    rulesets = construct_rulesets(rules, exemptions, use_dialects=dialects)
    output_dir = ctx.obj.get("output_dir")

    with closing(
            DatabaseUpdater(
                db=ctx.obj.get("database"),
                temp_tables=dialects
            )
    ) as db_obj:
        updated_lex = db_obj.update(rulesets)
    write_lex_per_dialect(updated_lex, output_dir, LEX_PREFIX, None)
    if check_phonemes:
        write_lex_per_dialect(
            updated_lex, output_dir, "invalid_transcriptions",
            validate_phonemes,
            valid_phonemes=ctx.obj["valid_phonemes"],
            return_transcriptions="invalid")


@main.command("compare")
@click.option(
    "-id",
    "--rule-id",
    "rule_ids",
    multiple=True,
    help="String to identify a specific rule to extract updates from. "
         "Format: <ruleset name>_<index number in the ruleset list>, or "
         "<ruleset name>, e.g. nasal_retroflex_1, or nasal_retroflex"
)
@click.pass_context
def compare_matching_updated_transcriptions(
        ctx, rule_ids):
    """Extract transcriptions before and after updates.

    By default, extract "before/after"-comparisons for all rules (`-r/--rules-file`).
    If `-id/--rule-id` option can be specified multiple times, to specify several rulesets or
    rules.
    """
    click.secho(f"Compare transcriptions before and after these transformation rules: \n"
                f"{rule_ids}", fg="cyan")
    logging.info("Rule_ids to select updates from:  %s", rule_ids)
    start = datetime.now()
    rules = load_data(ctx.obj.get("rules_file"))
    exemptions = load_data(ctx.obj.get("exemptions_file"))
    dialects = ctx.obj.get("dialects")
    rulesets = list(construct_rulesets(rules, exemptions, use_dialects=dialects))
    output_dir = ctx.obj.get("output_dir")

    with closing(
            DatabaseUpdater(db=ctx.obj.get("database"), temp_tables=dialects)
    ) as db_obj:
        df_gen = db_obj.select_updates(rulesets, rule_ids)
        try:
            comparison_df = pd.concat(df_gen, join="inner", ignore_index=True)
        except ValueError as e:
            logging.error("No output transcriptions. %s", e)
            click.secho("Done processing, no output.", fg="yellow")
            return
    #comparison = compare_transcriptions(matching_words, updated_words)
    end = datetime.now()
    column_map = {
        "p.unique_id": "unique_id",
        "p.nofabet": "transcription",
        "p.pron_id": "pron_id",
        COL_WORDFORM: "word",
    }
    comparison_df.rename(columns=column_map, inplace=True)
    for dialect in comparison_df.dialect.unique():
        filename = (output_dir / f"comparison_{dialect}.txt")
        comparison_df["arrow"] = "===>"
        columns = ["pron_id", "rule_id", "word", "transcription", "arrow", "new_transcription"]
        comparison_df[comparison_df["dialect"] == dialect][columns].to_csv(filename)
    click.secho(f"Done processing. "
                f"Output is in {output_dir}/comparison_*.txt files.",
                fg="cyan")
    click.secho(f"Processing time command: {str(end-start)}, Total time:"
                f" {str(datetime.now()-start)}",
                fg="red")


@main.command("insert")
@click.pass_context
def insert_newwords(ctx):
    """Insert new word entries to the lexicon."""
    click.secho("Add new words to database", fg="cyan")
    newwords = load_newwords(ctx.obj.get("newword_files"), newword_column_names)
    database = ctx.obj.get("database")
    dialects = ctx.obj.get("dialects")
    output_dir = ctx.obj.get("output_dir")
    with closing(
            DatabaseUpdater(
                db=database,
                temp_tables=dialects,
                newwords=newwords)
    ) as db_obj:
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
    "-sep",
    "--separate-forms",
    is_flag=True,
    help="Keep spoken and written forms of dialect transcriptions "
         "as separate MFA-formatted lexica."
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
def convert_format(ctx, lexicon_dir, separate_forms, spoken_prob, written_prob):
    """Convert lexicon formats to comply with MFA."""
    click.secho("Convert lexica to MFA dict format", fg="cyan")
    convert_lex_to_mfa(
        lex_dir=lexicon_dir,
        combine_dialect_forms=not separate_forms,
        probabilities=dict(
            written=written_prob,
            spoken=spoken_prob),
    )


def generate_new_lexica(
        new_rulesets=None,
        use_ruleset_areas=False,
        data_dir=".",
        lex_dir="lexica",
        db_path="backend-db03.db",
):
    """Generate updated lexica files with a list of new rule objects.

    Save the rules and exemptions to disk.
    Update the lexicon database with those files,
    and write the updated lexica to the "lexica" directory.
    Convert the format to be compatible with the MFA algorithm.

    Parameters
    ----------
    new_rulesets: list[Rule]
    use_ruleset_areas: bool
        If True, only generate lexica for the areas of the given rulesets.
        If False, update and write new lexicon files for all dialects.
    data_dir: str or Path
        Path for saving rules and exemptions to files
    lex_dir: str or Path
        Path for saving lexicon files
    db_path: str or Path
        Path to lexicon database
    """
    data_dir = ensure_path_exists(data_dir)
    try:
        # Lagre regelsettene til filer
        save_rules_and_exemptions(new_rulesets, output_dir=data_dir)
    except (TypeError, ValueError, AttributeError) as error:
        print(error)
        print("Generating lexica with existing rules from rules.py")

    rulesets = load_data(data_dir / "rules.py")
    exemptions = load_data(data_dir / "exemptions.py")
    rulesets = [RuleSet(**r_dict, exempt_words=exemptions) for r_dict in rulesets]
    dialects = list({d for r in rulesets for d in r.areas}) if use_ruleset_areas else \
        dialect_schema.schema

    with closing(
        DatabaseUpdater(
            db=db_path,
            temp_tables=dialects,)
    ) as db_obj:
        # Oppdater leksika med lexupdater
        updated_lex = db_obj.update(rulesets)
    write_lex_per_dialect(updated_lex, Path(lex_dir), LEX_PREFIX, None)
    # Konverter leksika til et format som passer FA-algoritmen
    convert_lex_to_mfa(
            lex_dir=lex_dir,
            dialects=dialects,
            combine_dialect_forms=True,
        )

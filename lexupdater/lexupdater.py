"""Transcription updates for a pronunciation lexicon in sqlite3 db format."""

import logging
import pathlib
import pprint
from contextlib import closing
from datetime import datetime
from pathlib import Path

import click
import pandas as pd

from lexupdater.dialect_updater import preprocess_rulefiles

from .constants import (
    LICIT_PHONES,
    newword_column_names,
    LEX_PREFIX,
    MATCH_PREFIX,
    NEW_PREFIX,
    dialect_schema,
    CHANGE_PREFIX
)
from .db_handler import DatabaseUpdater
from .rule_objects import (
    save_rules_and_exemptions,
    RuleSet,
    preprocess_rules
)
from .utils import (
    make_list,
    set_logging_config,
    write_lexicon,
    flatten_match_results,
    load_config,
    load_data,
    load_newwords,
    convert_lex_to_mfa,
    validate_phonemes,
    write_lex_per_dialect,
    ensure_path_exists,
    resolve_rel_path,
    write_tracked_update
)

CFG = {
    'database': 'data/nst_lexicon_bm.db',
    'output_dir': 'data/output',
    'dialects': [
        'e_spoken',
        'e_written',
        'sw_spoken',
        'sw_written',
        'w_spoken',
        'w_written',
        't_spoken',
        't_written',
        'n_spoken',
        'n_written'],
    'exemptions_file': 'exemptions.py',
    'newwords_path': 'newwords.csv',
    'rules_file': 'rules.py',
}
CONFIG_FILE = load_config("./config.py")
CFG.update(CONFIG_FILE)
CONTEXT_SETTINGS = dict(
    default_map=CFG,
    help_option_names=['-h', '--help'],
)
OUTPUT_DIR = ensure_path_exists(CFG.get("output_dir"))


def resolve_dir(ctx, param, path):
    if path is not None:
        return OUTPUT_DIR / path


def ensure_dir(ctx, param, path):
    if path.is_dir():
        return ensure_path_exists(path)
    return ensure_path_exists(OUTPUT_DIR)


def split_multiple_args(ctx, param, arg):
    """Create a list from an option parameter."""
    if arg is None:
        return
    if isinstance(arg, list):
        return [item for value in arg for item in make_list(value)]
    return make_list(arg)


def configure_logging(ctx, param, verbose):
    """Configure logging level and destination based on user input."""
    return set_logging_config(verbose, logfile=(OUTPUT_DIR/"log.txt"))


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option(
    "-db",
    "--database",
    type=click.Path(resolve_path=True, dir_okay=False, path_type=pathlib.Path),
    help="The path to the lexicon database.",
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
    "-n",
    "--newwords-path",
    type=click.Path(resolve_path=True, exists=True, path_type=pathlib.Path),
    help="Path to folder with csv files or to a single file with new words to add to the lexicon.",
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
def main(ctx, database, dialects, newwords_path, verbose):
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
    logging.info("START LOG")
    global CFG
    CFG.update(ctx.params)
    if verbose:
        click.secho("Configuration values:", fg="yellow")
        click.echo(pprint.pformat(CFG))
        click.echo(f"Invoked command: {ctx.invoked_subcommand}")

    if ctx.invoked_subcommand in ["original-lexicon"]:
        ctx.obj = db = DatabaseUpdater(db=database, temp_tables=[])
    else:
        newwords = load_newwords(newwords_path)
        click.echo("Initialise database")
        ctx.obj = db = DatabaseUpdater(db=database, temp_tables=dialects, newwords=newwords)

    @ctx.call_on_close
    def close_db():
        db.close()
        click.echo("DATABASE CLOSED")


@main.command("original-lexicon")
@click.option(
    "-o", "--outfile",
    type=click.Path(resolve_path=True, path_type=pathlib.Path),
    default="original_nst_lexicon_bm.csv",
    callback=resolve_dir,
)
@click.pass_obj
def write_original(db_obj, outfile):
    """Write the original lexicon database entries to file."""
    click.secho("Write the base lexicon to file.",
                fg="cyan")
    data = db_obj.get_original_data()
    write_lexicon(outfile, data)


@main.command("match", deprecated=True)
@click.pass_obj
def match_words(db_obj):
    """Fetch database entries that match the replacement rules."""
    click.secho("Fetch rows in the database that match the given rules",fg="cyan")
    # Preprocess input data
    rules_file = CFG.get("rules_file")
    exemptions_file = CFG.get("exemptions_file")
    dialects = CFG.get("dialects")
    rulesets, dialects = preprocess_rules(rules_file, exemptions_file)

    with closing(
            DatabaseUpdater(
                db=CFG.get("database"),
                temp_tables=dialects,
            )
    ) as db_obj:
        matches = db_obj.select_pattern_matches(rulesets)
    write_lex_per_dialect(
        matches, OUTPUT_DIR, MATCH_PREFIX, flatten_match_results)


@main.command("update", context_settings={"help_option_names":['-h', '--help']})
@click.option(
    "-r",
    "--rules-file",
    type=click.Path(resolve_path=True, exists=True, path_type=pathlib.Path),
    help="Apply replacement rules from the given file path.",
    default=CFG.get("rules_file")
)
@click.option(
    "-e",
    "--exemptions-file",
    type=click.Path(resolve_path=True, exists=True, path_type=pathlib.Path),
    help="Apply exemptions from the given file path to the rules.",
    default=CFG.get("exemptions_file")
)
@click.option(
    "-o",
    "--output-dir",
    type=click.Path(resolve_path=True, file_okay=False, path_type=pathlib.Path),
    help="The directory path that files are written to.",
    callback=ensure_dir,
)
@click.option(
    "-t", "--track-rules",
    type=str,
    multiple=True,
    callback=split_multiple_args,
    help="Extract transcriptions before and after updates by given rule ids, comma-separated"
)
@click.pass_obj
def update_dialects(db_obj, rules_file, exemptions_file, output_dir, track_rules):
    """Update dialect transcriptions with rules."""
    # Load data
    rulesets = preprocess_rulefiles(rules_file, exemptions_file)

    # Iterate through rules and run update queries
    if track_rules:
        click.secho(f"Track transcription changes for rules: {track_rules}", fg="cyan")
        tracked_updates = db_obj.update(rulesets, track_rules)
        for df in tracked_updates:
            write_tracked_update(df, output_dir)
    else:
        click.secho("Update dialect transcriptions", fg="cyan")
        db_obj.update(rulesets)

    # Write output to disk
    for dialect in db_obj.dialects:
        data = db_obj.get_dialect_data(dialect)
        filename = (output_dir / f"{dialect}_pronunciation_lexicon.csv")
        write_lexicon(filename, data)


@main.command("update-old", deprecated=True)
@click.option(
    "-p",
    "--check-phonemes",
    is_flag=True,
    help="Verify that all phonemes in the lexicon transcriptions are in the "
         "given phoneme inventory file, with one phoneme per line."
)
@click.pass_context
def update_dialects_old(ctx, check_phonemes):
    """Update dialect transcriptions with rules."""
    click.secho("Update dialect transcriptions", fg="cyan")
    start = datetime.now()
    rules_file = CFG.get("rules_file")
    exemptions_file = CFG.get("exemptions_file")
    rulesets, dialects = preprocess_rules(
        rules_file, exemptions_file, config_dialects=CFG.get("dialects"))

    with closing(
            DatabaseUpdater(
                db=CFG.get("database"),
                temp_tables=dialects
            )
    ) as db_obj:
        updated_lex = db_obj.update_old(rulesets)
    write_lex_per_dialect(updated_lex, OUTPUT_DIR, LEX_PREFIX, None)
    if check_phonemes:
        write_lex_per_dialect(
            updated_lex, OUTPUT_DIR, "invalid_transcriptions",
            validate_phonemes,
            valid_phonemes=LICIT_PHONES,
            return_transcriptions="invalid")
    end = datetime.now()
    click.secho(f"Done processing. "
                f"Output is in {OUTPUT_DIR}/{LEX_PREFIX}_*.txt files.",
                fg="cyan")
    click.secho(f"Processing time: {str(end-start)}",
                fg="yellow")


@main.command("track-changes", deprecated=True)
@click.argument(
    "rule_ids",
    nargs=-1,
    required=True
)
@click.pass_context
def track_rule_changes(ctx, rule_ids):
    """Extract transcriptions before and after updates by given rule_ids, and write to csv files.

    RULE_IDS format:    <ruleset name>_<.rules index number> or <ruleset name>
    Examples:           nasal_retroflex_0 retroflex errorfix_3
    """
    click.secho(f"Compare transcriptions before and after these transformation rules: \n"
                f"{rule_ids}", fg="cyan")
    start = datetime.now()
    rules_file = CFG.get("rules_file")
    exemptions_file = CFG.get("exemptions_file")
    rulesets, dialects = preprocess_rules(
        rules_file, exemptions_file, rule_ids, config_dialects=CFG.get("dialects"))

    with closing(
            DatabaseUpdater(db=CFG.get("database"), temp_tables=dialects)
    ) as db_obj:
        df_gen = db_obj.select_updates(rulesets, rule_ids)

        for df in df_gen:
            rule_id = df["rule_id"].unique()[0]
            dialect = df["dialect"].unique()[0]
            df["arrow"] = "===>"
            columns_to_write = {
                'dialect': 'dialect',
                'p.pron_id': 'pron_id',
                'rule_id': 'rule_id',
                'w.wordform': 'word',
                'p.nofabet': 'transcription',
                'arrow': 'arrow',
                'new_transcription': 'new_transcription'}
            filename = OUTPUT_DIR / f"transcription_changelog_{rule_id}.csv"
            try:
                df.to_csv(
                    filename,
                    columns=columns_to_write.keys(),
                    header=columns_to_write.values(),
                )
            except Exception as e:
                logging.error(e)
    click.echo("Done processing.")
    click.echo(f"Total time: {str(datetime.now()-start)}")

@main.command("newwords")
@click.option(
    "-o",
    "--outfile",
    type=click.Path(),
    default="lexicon_with_new_words.csv",
    help="File name where the updated lexicon will be saved.",
    callback=resolve_dir,
)
@click.pass_obj
def get_newwords(db_obj, outfile):
    """Write the new word entries from the lexicon db to disk."""
    click.secho("Add new words to database", fg="cyan")
    data = db_obj.get_newwords()
    write_lexicon(outfile, data)


@main.command("convert")
@click.option("-s", "--standards", default="nofabet,ipa,sampa")
@click.option("--filename")
@click.pass_context
def convert_transcriptions(ctx, standards, filename):
    pass


@main.command("insert", deprecated=True)
@click.pass_context
def insert_newwords_old(ctx):
    """Insert new word entries to the lexicon."""
    click.secho("Add new words to database", fg="cyan")
    newwords = load_newwords(CFG.get("newword_files"), newword_column_names)
    database = CFG.get("database")
    dialects = CFG.get("dialects")
    output_dir = CFG.get("output_dir")
    with closing(
            DatabaseUpdater(
                db=database,
                temp_tables=dialects,
                newwords=newwords)
    ) as db_obj:
        lex_with_newwords = db_obj.get_tmp_table_state()
    write_lexicon((output_dir / f"{NEW_PREFIX}.txt"), lex_with_newwords)


@main.command("convert-old", deprecated=True)
@click.option(
    "-l",
    "--lexicon-dir",
    type=click.Path(resolve_path=True, file_okay=False, path_type=pathlib.Path),
    callback=ensure_dir,
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
    """WARNING: Deprecated function.

    Generate updated lexica files with a list of new rule objects.

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
    logging.warning("WARNING: Deprecated function.")
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

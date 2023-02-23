"""Utility functions for lexupdater"""

import csv
import functools
import importlib
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Union, Iterable, List, Generator, Tuple, Dict

import autopep8
import click
import pandas as pd
from schema import Schema, SchemaError

from .constants import dialect_schema, MFA_PREFIX, LEX_PREFIX, exemption_schema, ruleset_schema, newword_column_names, CHANGE_PREFIX


def ensure_path_exists(path):
    """Make sure a directory exists and is a Path object."""
    path_obj = Path(path)
    path_obj.mkdir(exist_ok=True, parents=True)
    return path_obj


def get_filelist(dir_path: Path, suffix=".csv"):
    """Turn a directory path into a list of the Paths in it. Filter file types with ``suffix``."""
    return list(dir_path.glob(f"*{suffix}"))


def write_lexicon(output_file: Union[str, Path], data: Iterable, delimiter: str = ","):
    """Write a simple txt file with the results of the SQL queries.

    Parameters
    ----------
    delimiter: str
        character to separate items in a row
    output_file: str
        Name of the file to write data to
    data: Iterable[dict]
        A collection of dictionaries,
        where the 1st, 2nd, 3rd and 2nd to last elements are saved to disk
    """
    logging.info("Write lexicon data to %s", output_file)
    if isinstance(data, pd.DataFrame):
        data.to_csv(output_file, header=True, index=False)
    else:
        with open(output_file, 'w', encoding="utf-8", newline='') as csvfile:
            out_writer = csv.writer(csvfile, delimiter=delimiter)
            out_writer.writerows(data)


def write_tracked_update(df, output_dir, file_prefix=CHANGE_PREFIX):
    rule_id = df["rule_id"].unique()[0]
    df["arrow"] = "===>"
    columns = ['dialect', 'pron_id', 'rule_id', 'wordform', 'transcription', 'arrow', 'new_transcription']
    filename = output_dir / f"{file_prefix}_{rule_id}.csv"
    try:
        write_lexicon(filename, df[columns])
    except Exception as e:
        logging.error(e)


def write_lex_per_dialect(
        data, out_dir, file_prefix, preprocess, *args, **kwargs):
    """Wrapper for writing a lexicon file per dialect in the data.

    .txt-files get saved to out_dir with the given file_prefix + dialect

    Parameters
    ----------
    data: dict
        The keys are the names of dialects, values are the lexicon entries
    out_dir: Path
    file_prefix: str
    preprocess: callable
        Function to process the data with before writing it to the file.
    """
    for dialect, entries in data.items():
        if callable(preprocess):
            entries = preprocess(entries, *args, **kwargs)
        out_file = out_dir / f"{file_prefix}_{dialect}.txt"
        write_lexicon(out_file, entries)


def strip_ids(data_entries):
    """Strip away the number ID-entries."""
    return [line[1:-1] if isinstance(line[-1], int) else line
            for line in data_entries if line]


def flatten_match_results(data: Iterable) -> Generator:
    """Flatten a nested list of rule pattern matches.

    Parameters
    ----------
    data: Iterable[tuple]
        A collection of tuples, where the first element is the rule pattern,
        the second is the collection of lexicon rows
        that match the rule pattern
    """
    for rule, words in data:
        for item in words:
            yield [rule] + list(item)


def filter_list_by_list(check_list, filter_list):
    """Keep only elements from check_list if they exist in the filter_list."""
    filtered = [item for item in check_list if item in filter_list]
    return filtered


def filter_exclude(check_list, exclude_list):
    """Keep only elements from check_list if they do NOT exist in the exclude_list."""
    filtered = [item for item in check_list if item not in exclude_list]
    return filtered


def resolve_rel_path(file_rel_path: Union[str, Path]) -> Path:
    """Resolve the full path from a potential relative path to the local or parent directory."""

    full_path = Path(file_rel_path).resolve()
    if not full_path.exists():
        full_path = Path.cwd().parent / file_rel_path
    return full_path


def load_module_from_path(file_path):
    """Use importlib to load a module from a .py file path."""
    module_path = resolve_rel_path(file_path)
    assert module_path.suffix == ".py", (
            f"Inappropriate file type: {module_path.suffix} ({file_path})")
    module_name = module_path.stem

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_module_vars(module_path) -> List:
    """Return all public variables' values that are defined in a module."""
    module_vars = list(load_module_dict(module_path).values())
    return module_vars


def load_module_dict(module_path) -> Dict:
    """Load a dict of the public variables defined in a python module, ``{var_name:value}``."""
    module = load_module_from_path(module_path)
    module_dict = module.__dict__
    return {
        key: value for key, value in module_dict.items()
        if value and not key.startswith("_")
    }




def load_data(file_path: Union[str, Path]) -> List:
    """Load data from a python file path."""
    return load_module_vars(file_path)


def load_config(filename):
    """Load variable names (lower case) and their values as a dict from a .py file."""
    try:
        return {k.lower(): v for k, v in load_module_dict(filename).items()}
    except FileNotFoundError:
        return {}

def map_rule_exemptions(exemptions: List[str]) -> dict:
    """Reduce the list of exemption dictionaries to a single dictionary.

    The keys are the name of the corresponding ruleset,
    and the exempt words are the values.

    Parameters
    ----------
    exemptions: list
        list of dicts of the form ``{'ruleset': str, 'words': list}``
    """
    return {exemption.get("ruleset"): exemption.get("words")
        for exemption in exemptions
    }


def load_exemptions(file_path: Union[str, Path]) -> dict:
    """Load exemptions from a .py file and validate the dict objects."""
    exemptions = load_module_vars(file_path)
    exemptions = validate_objects(exemptions, exemption_schema)
    return map_rule_exemptions(exemptions)


def load_rules(file_path: Union[str, Path]) -> Generator:
    """Load rulesets from a .py file and validate the rule dicts."""
    rules = load_module_dict(file_path)

    for name, rule_dict in rules.items():
        try:
            ruleset_schema.validate(rule_dict)
        except (AssertionError, SchemaError) as error:
            logging.error("SKIPPING RULESET %s BECAUSE OF %s", name, type(error))
            logging.error("Error message: %s", error)
            continue
        yield rule_dict


def get_ruleset_order(rules_file):
    return re.findall(r"(\w+) ?= ?{" , rules_file.read_text())


def load_newwords(csv_path: Union[str, Path], column_names: str = None) -> pd.DataFrame:
    """Load csv file(s) with new words into a pandas DataFrame.

    These are the columns expected in the csv files:
        "token": the orthographic form
        "transcription": The primary phonetic transcription
        "alt_transcription_1-3": Alternative transcriptions. May be empty
        "pos": The POS tag
        "morphology": Morphological features. May be empty
        "update_info": The dataset or source of the words

    Parameters
    ----------
    csv_path: str or pathlib.Path
        Path to a folder of csv files or a single csv file with new words
    column_names: str
        Comma-delimited string of columns to include from the csv file(s)

    Returns
    -------
    pd.DataFrame
    """
    use_columns = (
        newword_column_names if column_names is None
        else make_list(column_names)
    )

    def _csv_to_df(file_path):
        return pd.read_csv(
            file_path, header=0, index_col=None, usecols=lambda x: x in use_columns
        )

    def _many_csvs_to_df(dir_path):
        _df_list = []
        file_list = get_filelist(dir_path)
        for path in file_list:
            try:
                df = _csv_to_df(path)
            except FileNotFoundError as error:
                logging.error("Skipping file %s: %s:%s", path, type(error), error)
                continue
            _df_list.append(df)
        return pd.concat(_df_list, axis=0, ignore_index=True)

    full_path = resolve_rel_path(csv_path)
    if full_path.is_file:
        return _csv_to_df(full_path)
    if full_path.is_dir:
        return _many_csvs_to_df(full_path)


def validate_objects(obj_list: list, obj_schema: Schema) -> list:
    """Use a Schema to validate a list of objects.

    If only some objects are valid,
    the invalid objects are filtered out from the returned list.
    """
    if isinstance(obj_schema.schema, dict):
        return [obj for obj in obj_list if obj_schema.is_valid(obj)]
    if isinstance(obj_schema.schema, list):
        try:
            return obj_schema.validate(obj_list)
        except SchemaError as error:
            logging.error("Couldn't validate list %s due to %s",
                          obj_list, error)
    return filter_list_by_list(obj_list, obj_schema.schema)


def matching_data_to_dict(entries: Iterable) -> Dict[str, Tuple[str]]:
    """Unpack results of select_pattern_matches, and map them to column names."""
    flat_data = flatten_match_results(entries)
    return dict(zip(("rule_id", "word", "transcription", "pron_id"), zip(*flat_data)))


def updated_data_to_dict(entries: tuple) -> Dict:
    """Convert the return value of fetch_dialect_updates to a dict of lists.

    Parameters
    ----------
    entries: tuple
        Tuple of tuples with data entries,
        with either four or six items per tuple.
    """

    try:
        word, pos, feats, pron = zip(*entries)
        return {
            "word": word,
            "pos": pos,
            "feats": feats,
            "new_transcription": pron
        }
    except ValueError:
        uid, word, pos, feats, pron, pron_id = zip(*entries)
        return {
            "unique_id": uid,
            "word": word,
            "pos": pos,
            "feats": feats,
            "new_transcription": pron,
            "pron_id": pron_id,
        }


def data_to_df(data: dict, update: bool = False):
    """Create a dataframe with results from DatabaseUpdater methods.

    If update, a df with updated records is created, else a df with
    records regex patterns and matches is created"""

    data_dict: dict = {}
    for dialect, entries in data.items():
        if update:
            entry_dict = updated_data_to_dict(entries)
        else:
            try:
                entry_dict = matching_data_to_dict(entries)
            except ValueError as error:
                logging.debug("Skipping dict: %s", error)
                continue
        for key, value in entry_dict.items():
            data_dict.setdefault(key, []).extend(value)
            row_count = len(value)
        data_dict.setdefault("dialect", []).extend([dialect] * row_count)

    return pd.DataFrame(data_dict)


def compare_transcriptions(matching_words, updated_words):
    """Create a dataframe with lexicon data from the transformation rules.

    Filter the updated_words, i.e. all lexicon transcriptions after update,
    by the matching_words, i.e. rows that were affected by the rules.

    Returns
    -------
    pd.Dataframe
        Dataframe with original and updated transcriptions and their wordforms.
    """
    logging.info("Start transcription comparison")
    matching_df = data_to_df(matching_words)
    updated_df = data_to_df(updated_words, update=True)

    comparison = matching_df.merge(
        updated_df, how='inner', on=["pron_id", "word", "dialect"])
    logging.info("Merged tables")
    return comparison


def format_rulesets_and_exemptions(ruleset_list: list) -> Tuple:
    """Format code strings that assign rulesets and exemptions to variables."""
    rules = ""
    exemptions = ""

    for ruleset in ruleset_list:
        timestamp = datetime.today().strftime("%Y%m%d_%H%M%S%f")
        rules += (
            f"\n"
            f"{ruleset.name} = {ruleset.to_dict()}"
            f"\n")
        exemptions += (
            f"\n"
            f"exemption_{timestamp} = {ruleset.create_exemption_dict()}"
            f"\n")
    rules = autopep8.fix_code(rules, options={'aggressive': 2})
    exemptions = autopep8.fix_code(exemptions, options={'aggressive': 2})
    return rules, exemptions


def convert_lex_to_mfa(
        lex_dir="lexica",
        dialects=dialect_schema.schema,
        in_file_prefix=LEX_PREFIX,
        out_file_prefix=MFA_PREFIX,
        combine_dialect_forms=True,
        probabilities=None
):
    """Convert lexica generated by lexupdater to a format
    that is compatible with the Montreal Forced Aligner algorithm.

    Parameters
    ----------
    lex_dir: str or Path
        Directory with lexicon files to convert
    dialects: list
        Dialects to convert lexica for.
    in_file_prefix: str
        First part of input lexicon filenames. Expecting the dialect name to
        follow.
    out_file_prefix:str
        First part of output lexicon filenames. Extended with dialect name.
    combine_dialect_forms: bool
        If True, merge spoken and written forms of each dialect's
        transcriptions into a single MFA dictionary.
    probabilities: dict[str, float]
        Probabilities to assign different pronunciation forms in the MFA
        lexicon. Defaults to equal values for spoken and written forms.
        MFA documentation:
        https://montreal-forced-aligner.readthedocs.io/en/latest/dictionary.html#dictionaries-with-pronunciation-probability
    """
    if probabilities is None:
        probabilities = {"spoken": 1.0, "written": 1.0}
    lex_dir = Path(lex_dir)
    logging.info("Converting lexica for %s to MFA format", dialects)
    files = list(lex_dir.iterdir())
    filename_pattern = re.compile(
        r"(?P<in_prefix>[\w_]+)_"
        r"(?P<dialect>"
        r"(?P<area>\w{1,2})_"
        r"(?P<form>spoken|written))"
    )
    matches = [re.match(filename_pattern, lex_file.name) for lex_file in files]
    formatted_lexica = defaultdict(dict)
    for lex_file, rgx_match in zip(files, matches):
        if rgx_match is None:
            continue
        prefix, dialect, area, form = rgx_match.groups()
        if prefix != in_file_prefix or dialect not in dialects:
            continue
        with open(lex_file, encoding="utf-8") as l_file:
            lexicon = l_file.readlines()
        if not combine_dialect_forms:
            formatted_lexicon = fetch_mfa_dict_items(lexicon)
            out_file = lex_dir / f"{out_file_prefix}_{dialect}.dict"
            logging.debug("Write reformatted lexicon to %s", out_file)
            write_lexicon(out_file, formatted_lexicon, delimiter=" ")
        else:
            formatted_lexica[area][form] = fetch_mfa_dict_items(
                lexicon, prob=probabilities.get(form)
            )
    if combine_dialect_forms:
        for area, form_dicts in formatted_lexica.items():
            combined_lexicon = [
                pron for word in zip(*form_dicts.values()) for pron in word
            ]
            out_file = lex_dir / f"{out_file_prefix}_{area}.dict"
            logging.debug("Write reformatted lexicon to %s", out_file)
            write_lexicon(out_file, combined_lexicon, delimiter=' ')


def replace_phonemes(transcription: str):
    """Substitute phonemes to be valid in the MFA algorithm."""
    sub1 = re.sub(r"\bRS\b", "SJ", transcription)
    sub2 = re.sub(r"\b_\b", "", sub1)
    return sub2


def fetch_mfa_dict_items(lexicon: list, prob: float = None):
    """Format a lexicon list for the Montreal Forced Aligner algorithm.

    Parameters
    ----------
    lexicon: Iterable
        Lexicon to convert: The list contains strings with tab-separated
        values, where the first value is the wordform and the last value is
        the transcription.
    prob: float
        Probability that will be assigned to the lexicon lines
    """
    for entry in lexicon:
        line = entry.split("\t")
        word = line[0]
        transcription = replace_phonemes(line[-1]).split()
        if prob is not None:
            yield (word, prob, *transcription)
        else:
            yield (word, *transcription)


def validate_phonemes(updated_lexicon: list, valid_phonemes: list,
                      return_transcriptions="valid"):
    """Validate phonemes in the updated transcriptions of the lexicon."""
    transcriptions: dict = {"valid": [], "invalid": []}
    for row in updated_lexicon:
        try:
            # The transcription is the last element in the row
            assert all(p in valid_phonemes for p in row[-1].split(" "))
            transcriptions["valid"].append(row)
        except AssertionError as error:
            logging.debug(
                "%s. Transcription contains invalid phonemes: %s",
                error, row[-1])
            transcriptions["invalid"].append(row)
    return transcriptions.get(return_transcriptions, [])


def add_placeholders(vals):
    """Create a string of question mark placeholders for sqlite queries."""
    return ', '.join('?' for _ in vals)


def coordinate_constraints(constraints, add_prefix: str = ''):
    coordination = ' AND '.join(c for c in constraints)
    return f" {add_prefix} {coordination}" if (add_prefix and coordination) else coordination


def make_list(value, segments=False):
    """Turn a string, list or other collection into a list.

    Split a string on comma, newline, whitespace(set segments=True) or characters.
    """
    if isinstance(value, list):
        return value
    elif isinstance(value, str):
        if segments:
            return value.split(" ")
        if "," in value:
            return [v.lstrip(" ").rstrip(" ") for v in value.split(",")]
        if "\n" in value:
            return value.rstrip("\n").lstrip("\n").split("\n")
        return [value]
    return list(value)


def time_process(f):
    """Take the time of the process from """
    def new_func(*args, **kwargs):

        start = datetime.now()
        result = f(*args, **kwargs)
        end = datetime.now()
        click.secho(f"Processing time: {str(end - start)}", fg="blue")
        return result

    functools.update_wrapper(new_func, f)
    return new_func


def log_level(verbosity: int):
    """Calculate the log level given by the number of -v flags.

    0 = logging.WARNING (30)
    1 = logging.INFO (20)
    2 = logging.DEBUG (10)
    """
    return (3 - verbosity) * 10 if verbosity in (0, 1, 2) else 10


def set_logging_config(verbose=False, logfile="log.txt"):
    """Configure logging level and destination based on user input."""
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            "%(asctime)s | %(levelname)s "
            "| %(module)s-%(funcName)s-%(lineno)04d | %(message)s"),
        datefmt='%Y-%m-%d %H:%M',
        filename=logfile,
        filemode='a')

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


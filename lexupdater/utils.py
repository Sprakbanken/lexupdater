"""Utility functions for lexupdater"""

import csv
import importlib
import logging
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Union, Iterable, List, Generator, Tuple, Dict

import autopep8
import pandas as pd
from schema import Schema, SchemaError


def write_lexicon(output_file: Union[str, Path], data: Iterable):
    """Write a simple txt file with the results of the SQL queries.

    Parameters
    ----------
    output_file: str
        Name of the file to write data to
    data: Iterable[dict]
        A collection of dictionaries,
        where the 1st, 2nd, 3rd and 2nd to last elements are saved to disk
    """
    if not data:    # Do not write empty data
        return
    logging.info("Write lexicon data to %s", output_file)
    with open(output_file, 'w', newline='') as csvfile:
        out_writer = csv.writer(csvfile, delimiter='\t')
        for item in data:
            out_writer.writerow(item)


def flatten_match_results(data: Iterable) -> Generator:
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


def filter_list_by_list(check_list, filter_list):
    """Keep only elements from check_list if they exist in the filter_list."""
    filtered = [_ for _ in check_list if _ in filter_list]
    return filtered


def load_module_from_path(file_path):
    """Use importlib to load a module from a .py file path."""
    module_path = Path(file_path)
    assert module_path.suffix == ".py"
    module_name = module_path.stem

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_vars_from_module(module):
    """Return all public variables that are defined in a module"""
    module_dict = module.__dict__
    # Gather all public variables, ignore private vars and dunder objects
    module_vars = [
        value for var, value in module_dict.items()
        if not var.startswith("_")
    ]
    return module_vars


def load_data(file_rel_path: Union[str, Path]) -> List:
    """Load a list of variables from the given data file.

    Parameters
    ----------
    file_rel_path: str or Path
        Relative path to a .py module

    Returns
    -------
    list
        The python objects that are specified in the given data file
    """
    try:
        cur_path = Path(__file__).parent
        full_path = cur_path.joinpath("..", file_rel_path).resolve()
        assert full_path.exists(), f"File doesn't exist {full_path}"
        assert full_path.suffix == ".py", (
            f"Inappropriate file type: {full_path.suffix}")
    except (FileNotFoundError, AssertionError):
        full_path = Path(file_rel_path).resolve()
        assert full_path.exists(), f"File doesn't exist {full_path}"
        assert full_path.suffix == ".py", (f"Inappropriate file type: "
                                           f"{full_path.suffix}")

    module = load_module_from_path(full_path)
    module_vars = load_vars_from_module(module)
    return module_vars


def load_newwords(csv_paths: list, column_names: list) -> pd.DataFrame:
    """Load lists of new words into a pandas DataFrame.

    New words to be added to the lexicon are specified in
    csv files, which are loaded into the dataframe "newwords".

    These are the columns of "newwords":
        "token": the orthographic form
        "transcription": The primary phonetic transcription
        "alt_transcription_1-3": Alternative transcriptions. May be empty
        "pos": The POS tag
        "morphology": Morphological features. May be empty

    The csv files may contain additional columns, but these will not be loaded
    into "newwords"

    Parameters
    ----------
    csv_paths: list
        List of csv files with new words
    column_names: list
        Names of the columns in the newword df

    Returns
    -------
    pd.DataFrame
    """
    _df_list = []

    for path in csv_paths:
        try:
            cur_path = Path(__file__).parent
            full_path = cur_path.joinpath("..", path).resolve()
            assert full_path.exists() and full_path.suffix == ".csv"
            new_word_df = pd.read_csv(
                full_path, header=0, index_col=None
            )
            # ignore columns in the column list if the csv doesn't contain them
            col_names = filter_list_by_list(column_names, new_word_df.columns)
            _df_list.append(new_word_df.loc[:, col_names])
        except (FileNotFoundError, AssertionError) as error:
            logging.error(error)
    return pd.concat(_df_list, axis=0, ignore_index=True)


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

def matching_data_to_dict(entries: dict) -> Dict[str, list]:
    """Convert results of select_words_matching_rules to a dict of lists."""
    flat_data = flatten_match_results(entries)
    patterns, words, transcriptions, pron_ids = zip(*flat_data)
    return {
        "pattern": patterns,
        "word": words,
        "transcription": transcriptions,
        "pron_id": pron_ids,
    }


def updated_data_to_dict(entries: tuple, ids_to_filter_by: list = None) -> Dict:
    """Convert the return value of update_results to a dict of lists.

    Parameters
    ----------
    entries: tuple
        Tuple of tuples with data entries,
        with either four or six items per tuple.
    ids_to_filter_by: list
        If given, only return data entries where the pron_id is in this list
    """
    if ids_to_filter_by is None:
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
    else:
        data_dict: dict = {}
        keys = ["unique_id", "word", "pos", "feats", "new_transcription",
                "pron_id"]
        for row in entries:
            if row[-1] not in ids_to_filter_by:
                continue
            for key, value in zip(keys, row):
                data_dict.setdefault(key, []).extend([value])

        return data_dict


def data_to_df(data: dict, update: bool = False, pron_ids: list = None):
    """Create a dataframe with results from DatabaseUpdater methods."""
    data_dict: dict = {}
    update = update if pron_ids is None else True
    for dialect, entries in data.items():
        if update:
            entry_dict = updated_data_to_dict(
                entries, ids_to_filter_by=pron_ids)
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


def compare_transcriptions(database_updater):
    """Create a dataframe with lexicon data from the transformation rules.

    Run both select and update queries on the lexicon database,
    and filter results by the transcriptions that are affected by the rules.

    Returns
    -------
    pd.Dataframe
        Dataframe with original and updated transcriptions and their wordforms.
    """

    # Select words matching the regex patterns
    matching_words = database_updater.select_words_matching_rules()
    # Update lexicon based on rules
    updated_words = database_updater.update(include_id=True)

    matching_df = data_to_df(matching_words)
    matching_pron_ids = matching_df["pron_id"].to_list()
    updated_df = data_to_df(updated_words, pron_ids=matching_pron_ids)

    comparison = matching_df.merge(
        updated_df, how='outer', on=["pron_id", "word", "dialect"]).dropna()
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
        in_file_prefix="updated_lexicon_",
        out_file_prefix="NST_nob_"
):
    """Convert the format of the lexicon files from lexupdater to a format
    that is compatible with the Montreal Forced Aligner algorithm.

    Parameters
    ----------
    lex_dir: str
        Name of directory where the lexica files are saved
    in_file_prefix: str
        First part of input lexicon filenames. Expecting the dialect name to
        follow.
    out_file_prefix:str
        First part of output lexicon filenames. Extended with dialect name.
    """
    def format_line(line):
        return f"{line[0]} {replace_phonemes(line[-1])}"

    def replace_phonemes(transcription: str):
        return re.sub(r"\bRS\b", " SJ ", transcription)

    directory = Path(lex_dir)

    print("Converting lexica for:")
    for lexicon_file in directory.glob(in_file_prefix + "*.txt"):
        dialect = re.match(in_file_prefix + r"(.*).txt",
                           lexicon_file.name).group(1)
        print(dialect)
        out_file = directory / (out_file_prefix + f"{dialect}.dict")
        with lexicon_file.open() as l_file, out_file.open("w") as fa_lf:
            lexicon = l_file.readlines()
            fa_dict_lines = [format_line(line.split("\t")) for line in lexicon]
            fa_lf.writelines(fa_dict_lines)

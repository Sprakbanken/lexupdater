"""Utility functions for lexupdater"""

import csv
import importlib.machinery
import importlib.util
import logging
from pathlib import Path
from typing import Union, Iterable, List, Generator

import pandas as pd


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


def load_module_from_path(file_path: Union[str, Path]):
    """Use importlib to load a module from a .py file path."""
    file_path = Path(file_path)
    assert file_path.suffix == ".py"
    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    exec_module = getattr(spec.loader, "exec_module")
    exec_module(module)
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
        assert full_path.exists() and full_path.suffix == ".py"
    except [FileNotFoundError, AssertionError] as error:
        logging.error(error)

    module = load_module_from_path(full_path)
    module_vars = load_vars_from_module(module)
    return module_vars


def _load_newwords(newword_csv_paths: list, column_names: list) -> pd.DataFrame:
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
    newword_csv_paths: list
        List of csv files with new words
    column_names: list
        Names of the columns in the newword df

    Returns
    -------
    pd.DataFrame
    """
    _df_list = []

    for path in newword_csv_paths:
        # TODO: Handle exception if csv doesn't contain columns in column list
        new_word_df = pd.read_csv(path, header=0, index_col=None)[column_names]
        _df_list.append(new_word_df)

    return pd.concat(_df_list, axis=0, ignore_index=True)

"""Utility functions for lexupdater"""

import csv
import importlib.machinery
import importlib.util
import logging
from pathlib import Path
from typing import Union, Iterable, Tuple, Any, List, Dict


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


def flatten_match_results(data: Iterable) -> Tuple:
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


def load_module_from_path(file_path: Union[str, Path]) -> Dict:
    """Use importlib to load a module from a .py file path."""
    assert Path(file_path).suffix == ".py"
    module_name = file_path.stem
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_data(file_rel_path: Union[str, Path]) -> List:
    """Load a list of variables from the given data file.

    Parameters
    ----------
    file_rel_path: str or Path
        Relative path to either a .toml or .py file

    Returns
    -------
    list
        The python objects that are specified in the given data file
    """
    cur_path = Path(__file__).parent
    full_path = cur_path.joinpath("..", file_rel_path)

    if full_path.suffix == ".py":
        module = load_module_from_path(full_path)
        module_dict = module.__dict__
        # Gather all public variables, ignore private vars and dunder objects
        return [
            value for var, value in module_dict.items()
            if not var.startswith("_")
        ]
    else:
        raise ValueError(f"Cannot load data from {full_path}")
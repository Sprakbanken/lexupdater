"""Test suite for helper functions in utils.py."""
from typing import Generator

import pandas as pd
import pytest

from lexupdater import utils


def test_write_lexicon(tmp_path):
    # given
    output_file = tmp_path / "some_file.txt"
    out_data = [["hello", "world", "this"], ["is", "a", "test"]]
    # when
    utils.write_lexicon(output_file, out_data)
    # then
    assert output_file.exists()
    assert output_file.read_text() == 'hello\tworld\tthis\nis\ta\ttest\n'


def test_flatten_match_results():
    # given
    words = [
        ("one", "line", "of db data"),
        ("another", "line", "of data")
    ]
    nested_structure = [
        ("nofabet regex pattern", words)
    ]
    expected = [
        ["nofabet regex pattern", "one", "line", "of db data"],
        ["nofabet regex pattern", "another", "line", "of data"]
    ]
    # when
    result = utils.flatten_match_results(nested_structure)
    # then
    assert isinstance(result, Generator)
    result_list = list(result)
    assert len(expected) == len(result_list)
    for result_element, expected_element in zip(result_list, expected):
        assert result_element == expected_element


def test_filter_list_by_list_all_valid(some_dialects, all_dialects):
    # given
    input_dialects = some_dialects + ["e_spoken"]
    # when
    result = utils.filter_list_by_list(input_dialects, all_dialects)
    # then
    assert result == input_dialects


def test_filter_list_by_list_not_valid(some_dialects, all_dialects):
    # given
    input_dialects = some_dialects + ["bergensk"]
    # when
    result = utils.filter_list_by_list(input_dialects, all_dialects)
    # then
    assert result == some_dialects


@pytest.fixture
def module_file_path(tmp_path):
    """Create a python file with dummy variables, and return the path."""
    file_path = (tmp_path / "dummy_module.py")
    module_content = """DATABASE = "a_database.db"
    OUTPUT_DIR = "delete_this_folder"
    RULES_FILE = "some_rules.py"
    EXEMPTIONS_FILE = "and_some_exemptions.py"
    NEWWORD_FILE = "all_brand_new_newwords.py"
    DIALECTS = [
        "norwegian_dialect",
    ]
    """
    file_path.write_text(module_content.replace(r"    ", ""))
    return str(file_path)


def test_load_module_from_path(module_file_path):
    # when
    result_module = utils.load_module_from_path(module_file_path)
    # then
    assert result_module.DATABASE == "a_database.db"
    assert result_module.OUTPUT_DIR == "delete_this_folder"
    assert result_module.RULES_FILE == "some_rules.py"
    assert result_module.EXEMPTIONS_FILE == "and_some_exemptions.py"
    assert result_module.NEWWORD_FILE == "all_brand_new_newwords.py"
    assert len(result_module.DIALECTS) == 1
    assert result_module.DIALECTS == ["norwegian_dialect"]


def test_load_module_from_path_raises_error():
    file_path = "wrong_path_extension.txt"
    # given
    with pytest.raises(AssertionError):
        # when
        utils.load_module_from_path(file_path)


def test_load_vars_from_module():
    # given
    import dummy_config
    # when
    result = utils.load_vars_from_module(dummy_config)
    # then
    assert isinstance(result, list)
    assert "tests/dummy_data.db" in result
    assert "tests/delete_me" in result
    assert "tests/dummy_rules.py" in result
    assert "tests/dummy_exemptions.py" in result
    assert ["n_written"] in result


def test_load_data(module_file_path):
    # when
    result = utils.load_data(module_file_path)
    # then
    # verify the same as for load_vars_from_module, but different values
    assert isinstance(result, list)
    assert "a_database.db" in result
    assert "delete_this_folder" in result
    assert "some_rules.py" in result
    assert "and_some_exemptions.py" in result
    assert "all_brand_new_newwords.py" in result
    assert ["norwegian_dialect"] in result


def test_load_data_raises_error():
    file_path = "wrong_path.txt"
    # given
    with pytest.raises(AssertionError):
        # when
        utils.load_data(file_path)


@pytest.mark.parametrize(
    "paths,col_names",
    [
        (["tests/dummy_newwords_2.csv"], ["token"]),
        (
            ["tests/dummy_newwords_1.csv", "tests/dummy_newwords_2.csv"],
            [
                "token",
                "transcription",
                "alt_transcription_1",
                "alt_transcription_2",
                "alt_transcription_3",
                "pos",
                "morphology"
            ]
        ),
        (["tests/dummy_newwords_2.csv"], ["word", "transcription", "feats"])
    ],
    ids=["minimal_input", "maximal_input", "wrong_input"]
)
def test_load_newwords(paths, col_names):
    # given
    valid_col_names = [
        "token",
        "transcription",
        "alt_transcription_1",
        "alt_transcription_2",
        "alt_transcription_3",
        "pos",
        "morphology"
    ]
    result = utils.load_newwords(paths, col_names)[:5]

    assert isinstance(result, pd.DataFrame)
    assert all([col in valid_col_names for col in result.columns])

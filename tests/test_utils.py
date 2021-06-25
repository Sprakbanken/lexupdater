"""Test suite for helper functions in utils.py."""
from pathlib import Path
from typing import Generator

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
    for result_element, expected_element in zip(result, expected):
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
    module_content = """DATABASE = "tests/dummy_data.db"
    OUTPUT_DIR = "tests/delete_me"
    RULES_FILE = "tests/dummy_rules.py"
    EXEMPTIONS_FILE = "tests/dummy_exemptions.py"
    NEWWORD_FILE = "tests/dummy_newword.py"
    DIALECTS = [
        "n_written",
    ]
    """
    file_path.write_text(module_content.replace(r"    ", ""))
    return str(file_path)


def test_load_module_from_path(module_file_path):
    # when
    result_module = utils.load_module_from_path(module_file_path)
    # then
    assert result_module.DATABASE == "tests/dummy_data.db"
    assert result_module.OUTPUT_DIR == "tests/delete_me"
    assert result_module.RULES_FILE == "tests/dummy_rules.py"
    assert result_module.EXEMPTIONS_FILE == "tests/dummy_exemptions.py"
    assert result_module.NEWWORD_FILE == "tests/dummy_newword.py"
    assert len(result_module.DIALECTS) == 1
    assert result_module.DIALECTS == ["n_written"]


def test_load_module_from_path_raises_error():
    file_path = "wrong_path_extension.txt"
    # given
    with pytest.raises(AssertionError) as error:
        # when
        result = utils.load_module_from_path(file_path)
        # then
        assert result is None
        assert error.value != 0


def test_load_vars_from_module():
    # given
    import dummy_config
    # when
    result = utils.load_vars_from_module(dummy_config)
    # then
    assert "tests/dummy_data.db" in result
    assert "tests/delete_me" in result
    assert "tests/dummy_rules.py" in result
    assert "tests/dummy_exemptions.py" in result
    assert "tests/dummy_newword.py" in result
    assert ["n_written"] in result


@pytest.mark.skip
def test_load_data(module_file_path):
    # when
    result = utils.load_data(module_file_path)
    assert False


def test_load_data_raises_error(module_file_path):
    # given
    with pytest.raises(AssertionError) as error:
        # when
        result = utils.load_data(module_file_path)
        assert error.value == 0


@pytest.mark.skip
def test__load_newwords():
    assert False

"""Test suite for helper functions in utils.py."""

import pytest

from lexupdater import utils


@pytest.mark.skip
def test_write_lexicon(tmp_path):
    # given
    output_file = tmp_path / "some_file.txt"
    out_data = [{"hello": "world", "this": "is", "a": "test"}]
    # when
    utils.write_lexicon(output_file, out_data)
    # then
    assert output_file.exists()
    assert output_file.read_text() == ""


@pytest.mark.skip
def test_flatten_match_results():
    # given
    nested_structure = []
    assert False


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


@pytest.mark.skip
def test_load_module_from_path():
    assert False


@pytest.mark.skip
def test_load_data():
    assert False


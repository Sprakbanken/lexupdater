"""Test suite for helper functions in utils.py."""
from lexupdater import utils


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

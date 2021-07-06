"""
Test suite for newword_updater.py
"""
import pytest
import pandas as pd

from pandera.errors import SchemaError

from lexupdater.newword_updater import parse_newwords
from lexupdater.constants import UNIQUE_ID_PATTERN

@pytest.fixture
def welformed_word_list():
    """A test example of a welformed newwords list"""
    testwords = {
        "token": ["dummyord-én", "dummyord-to"],
        "transcription": [
            "N EH2 T M OE3 RN AX0",
            "N EH2 T UU0 T G AA3 V AX0"
        ],
        "pos": ["NN", "NN"],
        "morphology": ["SIN|IND|NEU", "SIN|DEF|MAS"],
        "alt_transcription_1": [None, "N EH1 T UU0 T G AA3 V AX0"],
        "alt_transcription_2": [None, "N EH2 T UU0 T G EE3 V AX0"],
        "alt_transcription_3": [None, "N EH1 T UU0 T G EE3 V AX0"],
    }
    return pd.DataFrame(testwords)

@pytest.fixture
def missing_trans():
    """A test example of a newwords list with a missing primary transcription"""
    word = {
        "token": ["testord"],
        "transcription": [None],
        "pos": ["NN"],
        "morphology": [None],
        "alt_transcription_1": [None],
        "alt_transcription_2": [None],
        "alt_transcription_3": [None]
    }
    return pd.DataFrame(word)

@pytest.fixture
def missing_pos():
    """A test example of a newwords list with a pos tag"""
    word = {
        "token": ["testord"],
        "transcription": ["N EH1 T UU0 T G AA3 V AX0"],
        "pos": [None],
        "morphology": [None],
        "alt_transcription_1": [None],
        "alt_transcription_2": [None],
        "alt_transcription_3": [None]
    }
    return pd.DataFrame(word)

@pytest.fixture
def invalid_trans():
    """A test example of a newwords list with an invalid transcription"""
    word = {
        "token": ["testord"],
        "transcription": ["N EH1 T XX0 T G AA3 V AX0"],
        "pos": ["NN"],
        "morphology": [None],
        "alt_transcription_1": [None],
        "alt_transcription_2": [None],
        "alt_transcription_3": [None]
    }
    return pd.DataFrame(word)

#@pytest.mark.skip("Not implemented yet")
class TestNewwordUpdater(object):

    def test_with_valid_input(self, welformed_word_list):
        """
        Test that parse_newwords produces expected output with valid input
        """
        # when
        actual_wd_vals, actual_trans_vals = parse_newwords(
            welformed_word_list
        )
        expected_wd_vals = [
            (
                "dummyord-én",
                "NN",
                "SIN|IND|NEU",
                UNIQUE_ID_PATTERN.format(counter=0)
            ),
            (
                "dummyord-to",
                "NN",
                "SIN|DEF|MAS",
                UNIQUE_ID_PATTERN.format(counter=1)
            ),
        ]
        expected_trans_vals = [
            (
                "N EH2 T M OE3 RN AX0",
                UNIQUE_ID_PATTERN.format(counter=0),
                1
            ),
            (
                "N EH2 T UU0 T G AA3 V AX0",
                UNIQUE_ID_PATTERN.format(counter=1),
                1
            ),
            (
                "N EH1 T UU0 T G AA3 V AX0",
                UNIQUE_ID_PATTERN.format(counter=1),
                1
            ),
            (
                "N EH2 T UU0 T G EE3 V AX0",
                UNIQUE_ID_PATTERN.format(counter=1),
                1
            ),
            (
                "N EH1 T UU0 T G EE3 V AX0",
                UNIQUE_ID_PATTERN.format(counter=1),
                1
            ),
        ]
        # then
        assert len(actual_wd_vals) == len(expected_wd_vals)
        assert len(actual_trans_vals) == len(expected_trans_vals)
        for act, exp in zip(actual_wd_vals, expected_wd_vals):
            assert act == exp
        for act, exp in zip(actual_trans_vals, expected_trans_vals):
            assert act == exp

    def test_with_missing_trans(self, missing_trans):
        """
        Test that a missing primary transcription raises schema error
        """
        with pytest.raises(SchemaError):
            parse_newwords(missing_trans) 

    def test_with_missing_pos(self, missing_pos):
        """
        Test that a missing pos tag raises schema error
        """
        with pytest.raises(SchemaError):
            parse_newwords(missing_pos) 

    def test_with_invalid_trans(self, invalid_trans):
        """
        Test that an invalid transcription raises schema error
        """
        with pytest.raises(SchemaError):
            parse_newwords(invalid_trans) 

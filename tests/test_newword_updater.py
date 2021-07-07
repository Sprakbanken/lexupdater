"""
Test suite for newword_updater.py
"""
import pytest
import pandas as pd

from pandera.errors import SchemaError

from lexupdater.newword_updater import parse_newwords
from lexupdater.constants import UNIQUE_ID_PATTERN


class TestNewwordUpdater(object):

    def test_with_valid_input(self, wordlist_fixture):
        """
        Test that parse_newwords produces expected output with valid input
        """
        # when
        actual_wd_vals, actual_trans_vals = parse_newwords(
            wordlist_fixture
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

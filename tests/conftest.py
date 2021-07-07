"""Configuration values for the unit tests."""

from pathlib import Path
import pandas as pd

import pytest

from lexupdater.db_handler import DatabaseUpdater


@pytest.fixture(scope="session")
def ruleset_fixture():
    """Set up a test value for the rules."""
    from dummy_rules import test1, test2
    return [test1, test2]


@pytest.fixture(scope="session")
def exemptions_fixture():
    """Test value for the exemptions."""
    from dummy_exemptions import exemption1, exemption2
    return [exemption1, exemption2]


@pytest.fixture(scope="session")
def some_dialects():
    """Set up a test value for the dialects."""
    return ["e_spoken", "n_written", "sw_spoken"]


@pytest.fixture(scope="session")
def all_dialects():
    """Full list of valid dialects."""
    return [
        "e_spoken",
        "e_written",
        "sw_spoken",
        "sw_written",
        "w_spoken",
        "w_written",
        "t_spoken",
        "t_written",
        "n_spoken",
        "n_written",
    ]


@pytest.fixture(scope="session")
def wordlist_fixture():
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


@pytest.fixture(scope="session")
def missing_trans():
    """
    A test example of a newwords list with a missing primary transcription
    """
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


@pytest.fixture(scope="session")
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


@pytest.fixture(scope="session")
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


@pytest.fixture
def invalid_config_values(request, ruleset_fixture, exemptions_fixture):
    """Manipulated input data to test the schema validation."""
    if request.param == "rules":
        return (
            ruleset_fixture + [{"unexpected_key": "unexpected_value"}],
            exemptions_fixture,
        )
    elif request.param == "exemptions":
        return (
            ruleset_fixture,
            exemptions_fixture + [{"unexpected_key": "unexpected_value"}],
        )
    else:
        raise ValueError("invalid internal test config")


@pytest.fixture(scope="function")
def db_updater_obj(
    ruleset_fixture, all_dialects, exemptions_fixture, wordlist_fixture
        ):
    """Instance of the class object we want to test.

    Connect to the correct database, yield the DatabaseUpdater object,
    and close the connection after the test is done with the object.

    Tests that make use of this fixture will need to be updated
    if the config values are changed.
    """
    updater_obj = DatabaseUpdater(
        str(Path('tests') / 'dummy_data.db'),  # Ensure OS agnostic file path
        ruleset_fixture,
        all_dialects,
        exemptions=exemptions_fixture,
        newwords=wordlist_fixture,
    )
    yield updater_obj
    updater_obj.close_connection()

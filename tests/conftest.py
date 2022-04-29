"""Configuration values for the unit tests."""

from pathlib import Path
import pandas as pd

import pytest

from lexupdater.db_handler import DatabaseUpdater
from lexupdater.rule_objects import Rule, RuleSet


@pytest.fixture
def rule_fixture():
    """Dummy rule to be used in tests."""
    return Rule(
        pattern="transcription_pattern_to_replace",
        replacement=r"D DH \1 EE1",
        constraints=[
            {"field": "pos", "pattern": "value", "is_regex": True}
        ]
    )


@pytest.fixture
def proper_constraints():
    """List with a real-valued constraint dictionary."""
    return [{"field": "pos", "pattern": r"NN", "is_regex": False}]


@pytest.fixture
def ruleset_fixture(rule_fixture):
    """Dummy rule set object."""
    return RuleSet(
            name="test_rule_set",
            areas=["e_spoken"],
            rules=[rule_fixture],
            exempt_words=["exempt_word"]
        )

@pytest.fixture(scope="session")
def ruleset_list():
    """Set up a test value for the rules."""
    from dummy_rules import test1, test2
    return [test1, test2]


@pytest.fixture(scope="session")
def exemptions_list():
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
    """A test example of a newwords list with a missing pos tag"""
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
def invalid_config_values(request, ruleset_list, exemptions_list):
    """Manipulated input data to test the schema validation."""
    if request.param == "rules":
        return (
            ruleset_list + [{"unexpected_key": "unexpected_value"}],
            exemptions_list,
        )
    elif request.param == "exemptions":
        return (
            ruleset_list,
            exemptions_list + [{"unexpected_key": "unexpected_value"}],
        )
    else:
        raise ValueError("invalid internal test config")


@pytest.fixture(scope="function")
def db_updater_obj(
    ruleset_list, all_dialects, exemptions_list, wordlist_fixture
        ):
    """Instance of the class object we want to test.

    Connect to the correct database, yield the DatabaseUpdater object,
    and close the connection after the test is done with the object.

    Tests that make use of this fixture will need to be updated
    if the config values are changed.
    """
    updater_obj = DatabaseUpdater(str(Path('tests') / 'dummy_data.db'),
                                  all_dialects,
                                  rulesets=ruleset_list,
                                  newwords=wordlist_fixture,
                                  exemptions=exemptions_list)
    yield updater_obj
    updater_obj.close()

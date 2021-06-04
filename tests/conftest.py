"""Configuration values for the unit tests."""

from pathlib import Path

import pytest

from config import WORD_TABLE
from lexupdater.db_handler import DatabaseUpdater


@pytest.fixture(scope="session")
def ruleset_fixture():
    """Set up a test value for the rules"""
    return [
        {
            "areas": ["e_spoken"],
            "name": "retrotest",
            "rules": [
                {
                    "pattern": r"\b(R)([NTD])\\b",
                    "repl": r"\1 \2",
                    "constraints": [],
                },
                {
                    "pattern": r"\b(R)(NX0)\b",
                    "repl": r"\1 AX0 N",
                    "constraints": [],
                },
            ],
        },
        {
            "areas": ["n_written", "sw_spoken"],
            "name": "masc",
            "rules": [
                {
                    "pattern": r"\bAX0 R$",
                    "repl": r"AA0 R",
                    "constraints": [
                        {"field": "pos", "pattern": "NN", "is_regex": False},
                        {"field": "feats", "pattern": "MAS", "is_regex": True},
                    ],
                },
                {
                    "pattern": r"\bNX0 AX0$",
                    "repl": r"AA0 N AX0",
                    "constraints": [
                        {"field": "pos", "pattern": "NN", "is_regex": False},
                        {"field": "feats", "pattern": "MAS", "is_regex": True},
                    ],
                },
            ],
        },
    ]


@pytest.fixture(scope="session")
def some_dialects():
    """Set up a test value for the dialects"""
    return ["e_spoken", "n_written", "sw_spoken"]


@pytest.fixture(scope="session")
def all_dialects():
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
def exemptions_fixture():
    """Test value for the exemptions"""
    return [
        {"ruleset": "retrotest", "words": ["garn", "klarne"]},
        {"ruleset": "masc", "words": ["søknader", "søknadene"]},
    ]


@pytest.fixture
def invalid_config_values(request, ruleset_fixture, exemptions_fixture,
                          some_dialects):
    if request.param == "rules":
        return (
            ruleset_fixture + [{"unexpected_key": "unexpected_value"}],
            exemptions_fixture,
            some_dialects,
        )
    elif request.param == "exemptions":
        return (
            ruleset_fixture,
            exemptions_fixture + [{"unexpected_key": "unexpected_value"}],
            some_dialects,
        )
    elif request.param == "dialects":
        return (
            ruleset_fixture,
            exemptions_fixture,
            some_dialects + ["invalid_dialect"],
        )
    else:
        raise ValueError("invalid internal test config")


@pytest.fixture(scope="function")
def db_updater_obj(ruleset_fixture, all_dialects, exemptions_fixture):
    """Instance of the class object we want to test.

    Connect to the correct database, yield the DatabaseUpdater object,
    and close the connection after the test is done with the object.

    Tests that make use of this fixture will need to be updated
    if the config values are changed.
    """
    updater_obj = DatabaseUpdater(
        str(Path('tests') / 'dummy_data.db'),  # Ensure file path is OS agnostic
        ruleset_fixture,
        all_dialects,
        WORD_TABLE,
        exemptions_fixture,
    )
    yield updater_obj
    updater_obj.close_connection()

"""Configuration values for the unit tests."""

from pathlib import Path

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
def db_updater_obj(ruleset_fixture, all_dialects, exemptions_fixture):
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
        newwords=None,
    )
    yield updater_obj
    updater_obj.close_connection()

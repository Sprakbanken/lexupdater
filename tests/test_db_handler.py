"""
Test suite for all the classes in the db_handler.py module
"""
from unittest.mock import patch

import pytest
from schema import SchemaError

from config import DATABASE, WORD_TABLE
from lexupdater import db_handler


@pytest.mark.parametrize(
    "regex_pattern,expected", [(r"\bNX0 AX0$", True), (r"\bAX0 R$", False)]
)
def test_regexp(regex_pattern, expected):
    # given input
    string_item = "AEW0 T OH0 M OH0 B II1 L NX0 AX0"

    # when function is called
    result = db_handler.regexp(regex_pattern, string_item)

    # then compare results
    assert result == expected


class TestDatabaseUpdater:
    """
    Test suite for the DatabaseUpdater class
    """

    def test_database_updater(
        self, ruleset_fixture, some_dialects, exemptions_fixture
    ):
        """
        Test the constructor of the DatabaseUpdater
        with a patched _establish_connection function
        """
        # given
        with patch.object(
            db_handler.DatabaseUpdater, "_establish_connection", autospec=True
        ):
            # when
            result = db_handler.DatabaseUpdater(
                DATABASE,
                ruleset_fixture,
                some_dialects,
                WORD_TABLE,
                exemptions_fixture,
            )
            # then
            assert isinstance(result, db_handler.DatabaseUpdater)
            # Check that the patched function was called
            db_handler.DatabaseUpdater._establish_connection.assert_called()

    @pytest.mark.skip("invalid values do not raise issues upon initialisation")
    @pytest.mark.parametrize(
        "invalid_config_values",
        ["rules", "exemptions", "dialects"],
        indirect=True
    )
    def test_invalid_config_values_raises_error(self, invalid_config_values):
        """Test validation of rules and exemptions
        when loaded by DatabaseUpdater
        """
        # given
        rules, exemptions, dialects = invalid_config_values
        with patch.object(
            db_handler.DatabaseUpdater, "_establish_connection", autospec=True
        ):
            with pytest.raises(SchemaError):
                db_handler.DatabaseUpdater(
                    DATABASE,
                    rules,
                    dialects,
                    WORD_TABLE,
                    exemptions,
                )

    def test_establish_connection(
        self, ruleset_fixture, some_dialects, exemptions_fixture
    ):
        """Test the constructor of the DatabaseUpdater
        with patched elements for the _establish_connection function
        """
        # patch functions that are called by _establish_connection
        with patch(
            "lexupdater.db_handler.sqlite3", autospec=True
        ) as patched_sqlite:
            # given
            patch_connection = patched_sqlite.connect.return_value
            patch_cursor = patch_connection.cursor.return_value

            # when
            _ = db_handler.DatabaseUpdater(
                DATABASE,
                ruleset_fixture,
                some_dialects,
                WORD_TABLE,
                exemptions_fixture,
            )
            # then
            # Check that the patched functions were called
            patched_sqlite.connect.assert_called_with(DATABASE)
            patch_connection.create_function.assert_called()
            patch_connection.cursor.assert_called()
            patch_cursor.execute.assert_called()

    def test_select_words_matching_rules(self, db_updater_obj):
        # given
        assert all(result == [] for result in db_updater_obj.results.values())
        # when
        db_updater_obj.select_words_matching_rules()
        # then
        assert any([result != [] for result in db_updater_obj.results.values()])

    def test_update(self, db_updater_obj):
        # given
        assert all(result == [] for result in db_updater_obj.results.values())
        # when
        db_updater_obj.update()
        # then
        assert any([result != [] for result in db_updater_obj.results.values()])

    def test_update_results(self, db_updater_obj, all_dialects):
        # given
        test_dialect_name = sorted(list(all_dialects))[0]
        # when
        db_updater_obj.update_results()
        # then
        assert isinstance(db_updater_obj.results, dict)
        assert sorted(db_updater_obj.results.keys()) == sorted(all_dialects)
        assert len(db_updater_obj.results.get(test_dialect_name)[0]) == 20

"""Test suite for all the classes in the db_handler.py module."""

from unittest.mock import patch

import pytest

from dummy_config import DATABASE
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
        with a patched _connect_and_populate function
        """
        # given
        with patch.object(
            db_handler.DatabaseUpdater, "_connect_and_populate", autospec=True
        ):
            # when
            result = db_handler.DatabaseUpdater(
                DATABASE,
                ruleset_fixture,
                some_dialects,
                exemptions_fixture,
            )
            # then
            assert isinstance(result, db_handler.DatabaseUpdater)
            # Check that the patched function was called
            db_handler.DatabaseUpdater._connect_and_populate.assert_called()

    def test_connect_and_populate(
        self, ruleset_fixture, some_dialects,
        exemptions_fixture, wordlist_fixture
    ):
        """Test the constructor of the DatabaseUpdater."""
        # patch functions that are called by _connect_and_populate
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
                exemptions=exemptions_fixture,
                newwords=wordlist_fixture,
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
        assert any(
            [result != [] for result in db_updater_obj.results.values()]
        )

    def test_update(self, db_updater_obj):
        # given
        assert all(result == [] for result in db_updater_obj.results.values())
        # when
        db_updater_obj.update()
        # then
        assert any(
            [result != [] for result in db_updater_obj.results.values()]
        )

    def test_update_results(self, db_updater_obj, all_dialects):
        # given
        test_dialect_name = sorted(list(all_dialects))[0]
        # when
        db_updater_obj.update_results()
        # then
        assert isinstance(db_updater_obj.results, dict)
        assert sorted(db_updater_obj.results.keys()) == sorted(all_dialects)
        assert len(db_updater_obj.results.get(test_dialect_name)[0]) == 4

    def test_get_base(self, db_updater_obj):
        # when
        result = db_updater_obj.get_base()
        # then
        assert result is not None
        assert isinstance(result, list)
        assert result != []
        assert result[0] is not None

    def test__insert_newwords(self, db_updater_obj, wordlist_fixture):
        # when
        db_updater_obj.update_results()
        results = db_updater_obj.results
        input_words = wordlist_fixture["token"]
        main_trans = wordlist_fixture["transcription"]
        alt_trans = [
            x[1] for x in [
                wordlist_fixture["alt_transcription_1"],
                wordlist_fixture["alt_transcription_2"],
                wordlist_fixture["alt_transcription_3"]
            ]
        ]
        # then
        for d in results.keys():
            result_words = [x[0] for x in results[d]]
            result_trans = [x[3] for x in results[d]]
            assert all(wd in result_words for wd in input_words)
            assert all(tn in result_trans for tn in main_trans)
            assert all(tn in result_trans for tn in alt_trans)
"""
Test suite for all the classes in the db_handler.py module
"""
from unittest.mock import patch

import pytest
from schema import SchemaError

from lexupdater import config
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
                config.database,
                ruleset_fixture,
                some_dialects,
                config.word_table,
                exemptions_fixture,
            )
            # then
            assert isinstance(result, db_handler.DatabaseUpdater)
            # Check that the patched function was called
            db_handler.DatabaseUpdater._establish_connection.assert_called()

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
                    config.database,
                    rules,
                    dialects,
                    config.word_table,
                    exemptions,
                )

    def test_validate_dialect(self, db_updater_obj, some_dialects):
        # given
        input_dialects = some_dialects + ["e_spoken"]
        # when
        result = db_updater_obj.validate_dialects(input_dialects)
        # then
        assert result == input_dialects

    def test_validate_dialect_raises_error(self, db_updater_obj, some_dialects):
        # given
        input_dialects = some_dialects + ["bergensk"]
        # when
        result = db_updater_obj.validate_dialects(input_dialects)
        # then
        assert result == some_dialects

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
                config.database,
                ruleset_fixture,
                some_dialects,
                config.word_table,
                exemptions_fixture,
            )
            # then
            # Check that the patched functions were called
            patched_sqlite.connect.assert_called_with(config.database)
            patch_connection.create_function.assert_called()
            patch_connection.cursor.assert_called()
            patch_cursor.execute.assert_called()

    def test_construct_update_queries(self, db_updater_obj):
        # given
        expected_query = (
            "UPDATE e_spoken SET nofabet = REGREPLACE(?,?,nofabet) "
            "WHERE word_id IN (SELECT word_id "
            "FROM words_tmp WHERE wordform NOT IN (?,?));"
        )
        expected_values = ("\\b(R)([NTD])\\\\b", "\\1 \\2", "garn", "klarne")

        # when
        result = db_updater_obj.construct_update_queries()
        query, values = next(result)
        # then
        assert query == expected_query
        assert values == expected_values

    def test_update(self, db_updater_obj):
        # given
        updates = [(
            "UPDATE e_spoken SET nofabet = REGREPLACE(?,?,nofabet) "
            "WHERE word_id IN (SELECT word_id "
            "FROM words_tmp WHERE wordform NOT IN (?,?));",
            ("\\b(R)([NTD])\\\\b", "\\1 \\2", "garn", "klarne")
        )]
        # when
        with patch(
                "lexupdater.db_handler.DatabaseUpdater.construct_update_queries"
        ) as patched_func:
            patched_func.return_value = updates
            db_updater_obj.update()
        # then
        patched_func.assert_called_once()

    def test_get_results(self, db_updater_obj, all_dialects):
        # given
        test_dialect_name = sorted(list(all_dialects))[0]
        # when
        result = db_updater_obj.get_results()
        # then
        assert isinstance(result, dict)
        assert sorted(result.keys()) == sorted(all_dialects)
        assert len(result.get(test_dialect_name)[0]) == 20

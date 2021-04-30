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


def test_create_dialect_table_stmts():
    # given
    # deliberately choosing dialect names we don't use in the tool
    input_list = [
        "trøndersk",
        "bergensk",
    ]
    # when
    result = db_handler.create_dialect_table_stmts(input_list)
    # then
    assert "CREATE TEMPORARY TABLE trøndersk" in result[0][0]
    assert "INSERT INTO trøndersk" in result[0][1]
    assert "CREATE TEMPORARY TABLE bergensk" in result[1][0]
    assert "INSERT INTO bergensk" in result[1][1]


def test_create_word_table_stmts():
    # given
    input_word = "word_table_name"
    # when
    result_c, result_i = db_handler.create_word_table_stmts(input_word)
    # then
    assert "CREATE TEMPORARY TABLE word_table_name" in result_c
    assert "INSERT INTO word_table_name" in result_i


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
        "invalid_config_values", ["rules", "exemptions", "dialects"], indirect=True
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
        with pytest.raises(SchemaError):
            result = db_updater_obj.validate_dialects(input_dialects)
            # then
            assert result is None

    def test_establish_connection(
        self, ruleset_fixture, some_dialects, exemptions_fixture
    ):
        """Test the constructor of the DatabaseUpdater
        with patched elements for the _establish_connection function
        """
        # patch functions that are called by _establish_connection
        with patch(
            "lexupdater.db_handler.sqlite3", autospec=True
        ) as patched_sqlite, patch(
            "lexupdater.db_handler.create_word_table_stmts", autospec=True
        ) as p_word_tbl, patch(
            "lexupdater.db_handler.create_dialect_table_stmts", autospec=True
        ) as p_dialect_tbl:
            # given
            p_word_tbl.return_value = ("some string here", "another string here")
            p_dialect_tbl.return_value = [
                ("dialect string here", "another dialect string here")
            ] * len(some_dialects)
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
            p_word_tbl.assert_called_with(config.word_table)
            p_dialect_tbl.assert_called_with(some_dialects)

            patch_connection.create_function.assert_called()
            patch_connection.cursor.assert_called()

            patch_cursor.execute.assert_any_call("some string here")
            patch_cursor.execute.assert_any_call("another string here")
            patch_cursor.execute.assert_any_call("dialect string here")
            patch_cursor.execute.assert_any_call("another dialect string here")

    def test_construct_update_queries(self, db_updater_obj):
        # given
        # TODO: Refactor code so we can test smaller values at a time
        expected = {
            "query": "UPDATE e_spoken SET nofabet = REGREPLACE(?,?,nofabet) "
            "WHERE word_id IN (SELECT word_id "
            "FROM words_tmp WHERE wordform NOT IN (?,?));",
            "values": ["\\b(R)([NTD])\\\\b", "\\1 \\2", "garn", "klarne"],
            "is_constrained": False,
        }
        # when
        db_updater_obj._construct_update_queries()
        result = db_updater_obj._updates[0][0]
        # then
        assert all(
            [actual == exp for actual, exp in zip(result.items(), expected.items())]
        )

    def test_update(self, db_updater_obj):
        # given
        expected_first_item = (
            "UPDATE e_spoken SET nofabet = REGREPLACE(?,?,nofabet) "
            "WHERE word_id IN (SELECT word_id "
            "FROM words_tmp "
            "WHERE wordform NOT IN (?,?));",
            ("\\b(R)([NTD])\\\\b", "\\1 \\2", "garn", "klarne"),
        )
        # when
        result = db_updater_obj.update()
        # then
        assert result[0] == expected_first_item

    def test_get_results(self, db_updater_obj, all_dialects):
        # given
        test_dialect_name = sorted(list(all_dialects))[0]
        # when
        result = db_updater_obj.get_results()
        # then
        assert isinstance(result, dict)
        assert sorted(result.keys()) == sorted(all_dialects)
        assert len(result.get(test_dialect_name)[0]) == 20

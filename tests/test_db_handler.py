import unittest

import pytest

from lexupdater.db_handler import regexp, create_dialect_table_stmts, create_word_table_stmts


@pytest.mark.parametrize("regex_pattern,expected", [(r"\bNX0 AX0$", True), (r'\bAX0 R$', False)])
def test_regexp(regex_pattern, expected):
    # given input
    string_item = "AEW0 T OH0 M OH0 B II1 L NX0 AX0"

    # when function is called
    result = regexp(regex_pattern, string_item)

    # then compare results
    assert result == expected


def test_create_dialect_table_stmts():
    # given
    input_list = ["trøndersk", "bergensk"]  # deliberately choosing dialect names we don't use in the tool
    expected = [("""CREATE TEMPORARY TABLE trøndersk (
                    pron_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pron_id INTEGER NOT NULL,
                    word_id INTEGER NOT NULL,
                    nofabet TEXT NOT NULL,
                    certainty INTEGER NOT NULL,
                    FOREIGN KEY(word_id) REFERENCES words(word_id) ON UPDATE CASCADE);""",
                 "INSERT INTO trøndersk SELECT * FROM base;"
                 ),
                ("""CREATE TEMPORARY TABLE bergensk (
                    pron_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pron_id INTEGER NOT NULL,
                    word_id INTEGER NOT NULL,
                    nofabet TEXT NOT NULL,
                    certainty INTEGER NOT NULL,
                    FOREIGN KEY(word_id) REFERENCES words(word_id) ON UPDATE CASCADE);""",
                 "INSERT INTO bergensk SELECT * FROM base;"
                 )]
    # when
    result = create_dialect_table_stmts(input_list)
    # then
    assert result[0][0] == expected[0][0], expected[0][0]
    assert result[0][1] == expected[0][1]
    assert result[1][0] == expected[1][0], expected[1][0]
    assert result[1][1] == expected[1][1]


def test_create_word_table_stmts():
    # given
    input_word = "word_table_name"
    expected_create_stmt = f'''CREATE TEMPORARY TABLE word_table_name (
                    word_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    wordform TEXT NOT NULL,
                    pos TEXT,
                    feats TEXT,
                    source TEXT,
                    decomp_ort TEXT,
                    decomp_pos TEXT,
                    garbage TEXT,
                    domain TEXT,
                    abbr TEXT,
                    set_name TEXT,
                    style_status TEXT,
                    inflector_role TEXT,
                    inflector_rule TEXT,
                    morph_label TEXT,
                    compounder_code TEXT,
                    update_info TEXT);'''
    exected_insert_stmt = f"INSERT INTO word_table_name SELECT * FROM words;"
    # when
    result_create_stmt, result_insert_stmt = create_word_table_stmts(input_word)
    # then
    assert result_create_stmt == expected_create_stmt
    assert result_insert_stmt == exected_insert_stmt



@unittest.skip
class TestDatabaseUpdater():
    """
    Test suite for the DatabaseUpdater class
    """

    def test_database_updater(self):
        self.fail()

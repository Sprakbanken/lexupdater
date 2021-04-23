import unittest
from unittest.mock import patch

import pytest

from lexupdater import config
from lexupdater import db_handler


@pytest.mark.parametrize("regex_pattern,expected", [(r"\bNX0 AX0$", True), (r'\bAX0 R$', False)])
def test_regexp(regex_pattern, expected):
    # given input
    string_item = "AEW0 T OH0 M OH0 B II1 L NX0 AX0"

    # when function is called
    result = db_handler.regexp(regex_pattern, string_item)

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
    result = db_handler.create_dialect_table_stmts(input_list)
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
    result_create_stmt, result_insert_stmt = db_handler.create_word_table_stmts(input_word)
    # then
    assert result_create_stmt == expected_create_stmt
    assert result_insert_stmt == exected_insert_stmt


class TestDatabaseUpdater:
    """
    Test suite for the DatabaseUpdater class
    """

    @pytest.fixture(scope="class")
    def ruleset_fixture(self):
        """Set up a test value for the rules"""
        return [{'areas': ['e_spoken'],
                 'name': 'retrotest',
                 'rules': [{'pattern': r'\b(R)([NTD])\\b',
                            'repl': r'\1 \2',
                            'constraints': []},
                           {'pattern': r'\b(R)(NX0)\b',
                            'repl': r'\1 AX0 N',
                            'constraints': []}]},

                {'areas': ['n_written', 'sw_spoken'],
                 'name': 'masc',
                 'rules': [{'pattern': r'\bAX0 R$',
                            'repl': r'AA0 R',
                            'constraints': [{'field': 'pos', 'pattern': 'NN', 'is_regex': False},
                                            {'field': 'feats', 'pattern': 'MAS', 'is_regex': True}]},
                           {'pattern': r'\bNX0 AX0$',
                            'repl': r'AA0 N AX0',
                            'constraints': [{'field': 'pos', 'pattern': 'NN', 'is_regex': False},
                                            {'field': 'feats', 'pattern': 'MAS', 'is_regex': True}]}]}]

    @pytest.fixture(scope="class")
    def dialects_fixture(self):
        """Set up a test value for the dialects. Select either all, or only a few dialects to test with"""
        all_dialects = ['e_spoken', 'e_written',
                        'sw_spoken', 'sw_written',
                        'w_spoken', 'w_written',
                        't_spoken', 't_written',
                        'n_spoken', 'n_written']
        some_dialects = ['e_spoken', 'n_written', 'sw_spoken']
        return some_dialects

    @pytest.fixture(scope="class")
    def blacklists_fixture(self):
        """Set up a test value for the blacklists"""
        return [{
            'ruleset': 'retrotest',
            'words': ['garn', 'klarne']
        }, {
            'ruleset': 'masc',
            'words': ['søknader', 'søknadene', 'dugnader', 'dugnadene']
        }]

    @pytest.fixture(scope="class")
    def database_updater_fixture(self, ruleset_fixture, dialects_fixture, blacklists_fixture):
        """Set up an instance of the class object we want to test,
        connect to the correct database, yield the DatabaseUpdater object,
        and close the connection after the test is done with the object.

        Tests that use this fixture will need to be updated if the config values are changed.
        """
        updater_obj = db_handler.DatabaseUpdater(
            config.database, ruleset_fixture, dialects_fixture, config.word_table, blacklists_fixture
        )
        yield updater_obj
        updater_obj._connection.close()

    def test_database_updater_patch_private_method(self, ruleset_fixture, dialects_fixture, blacklists_fixture):
        """
        Test the constructor of the DatabaseUpdater
        with a patched _establish_connection function
        """
        # given
        with patch.object(db_handler.DatabaseUpdater, '_establish_connection', autospec=True):
            # when
            result = db_handler.DatabaseUpdater(
                config.database, ruleset_fixture, dialects_fixture, config.word_table, blacklists_fixture
            )
            # then
            assert isinstance(result, db_handler.DatabaseUpdater)
            # Check private attribute values
            assert result._db == "./data/input/backend-db02.db"
            assert result._word_table == "words_tmp"
            # Check list equality
            assert len(result._rulesets) == len(ruleset_fixture)
            assert result._rulesets == ruleset_fixture
            assert len(result._blacklists) == len(blacklists_fixture)
            assert result._blacklists == blacklists_fixture
            assert len(result._dialects) == len(dialects_fixture)
            assert result._dialects == dialects_fixture
            # Check that the patched function was called
            db_handler.DatabaseUpdater._establish_connection.assert_called()

    def test__validate_dialect(self, database_updater_fixture):
        # given
        input_dialect = "e_spoken"
        # when
        result = database_updater_fixture._validate_dialect(input_dialect)
        # then
        assert result == input_dialect

    def test__validate_dialect_raises_ValueError(self, database_updater_fixture):
        # given
        input_dialect = "bergensk"
        expected_error_message = f"{input_dialect} is not a valid dialect"
        # when
        with pytest.raises(ValueError) as errorinfo:
            result = database_updater_fixture._validate_dialect(input_dialect)
            # then
            assert expected_error_message in str(errorinfo.value)
            assert result is None

    def test__establish_connection(self, ruleset_fixture, dialects_fixture, blacklists_fixture):
        """Test the constructor of the DatabaseUpdater
        with patched elements for the _establish_connection function
        """
        # given "fake" objects/functions that are called by _establish_connection
        with patch("lexupdater.db_handler.sqlite3", autospec=True) as patched_sqlite, \
                patch("lexupdater.db_handler.create_word_table_stmts", autospec=True) as patched_word_tbl, \
                patch("lexupdater.db_handler.create_dialect_table_stmts", autospec=True) as patched_dialect_tbl:
            patched_word_tbl.return_value = ("some string here", "another string here")
            patched_dialect_tbl.return_value = [("dialect string here", "another dialect string here")] * len(
                dialects_fixture)
            patch_connection = patched_sqlite.connect.return_value
            patch_cursor = patch_connection.cursor.return_value

            # when
            _ = db_handler.DatabaseUpdater(
                config.database, ruleset_fixture, dialects_fixture, config.word_table, blacklists_fixture
            )
            # then
            # Check that the patched functions were called
            patched_sqlite.connect.assert_called()
            patched_sqlite.connect.assert_called_with("./data/input/backend-db02.db")

            patched_word_tbl.assert_called_with(config.word_table)
            patched_dialect_tbl.assert_called_with(dialects_fixture)

            patch_connection.create_function.assert_called()
            patch_connection.cursor.assert_called()

            patch_cursor.execute.assert_any_call("some string here")
            patch_cursor.execute.assert_any_call("another string here")
            patch_cursor.execute.assert_any_call("dialect string here")
            patch_cursor.execute.assert_any_call("another dialect string here")

    def test__construct_update_queries(self, database_updater_fixture):
        # given
        updater_obj = database_updater_fixture
        expected_updates = [[{
            'query': 'UPDATE e_spoken SET nofabet = REGREPLACE(?,?,nofabet) '
                     'WHERE word_id IN (SELECT word_id '
                     'FROM words_tmp WHERE wordform NOT IN (?,?));',
            'values': [
                '\\b(R)([NTD])\\\\b', '\\1 \\2', 'garn', 'klarne'
            ],
            'is_constrained': False
        }, {
            'query': 'UPDATE e_spoken SET nofabet = REGREPLACE(?,?,nofabet) '
                     'WHERE word_id IN (SELECT word_id '
                     'FROM words_tmp WHERE wordform NOT IN (?,?));',
            'values': [
                '\\b(R)(NX0)\\b', '\\1 AX0 N', 'garn', 'klarne'
            ],
            'is_constrained': False
        }], [{
            'query': 'UPDATE n_written SET nofabet = REGREPLACE(?,?,nofabet) '
                     'WHERE word_id IN (SELECT word_id FROM words_tmp '
                     'WHERE pos = ? AND feats REGEXP ? AND wordform NOT IN (?,?,?,?));',
            'values': [
                '\\bAX0 R$', 'AA0 R', 'NN', 'MAS', 'søknader', 'søknadene', 'dugnader', 'dugnadene'
            ],
            'is_constrained': True
        }, {
            'query': 'UPDATE sw_spoken SET nofabet = REGREPLACE(?,?,nofabet) '
                     'WHERE word_id IN (SELECT word_id FROM words_tmp '
                     'WHERE pos = ? AND feats REGEXP ? AND wordform NOT IN (?,?,?,?));',
            'values': ['\\bAX0 R$', 'AA0 R', 'NN', 'MAS', 'søknader', 'søknadene', 'dugnader', 'dugnadene'],
            'is_constrained': True
        }, {
            'query': 'UPDATE n_written SET nofabet = REGREPLACE(?,?,nofabet) '
                     'WHERE word_id IN (SELECT word_id FROM words_tmp '
                     'WHERE pos = ? AND feats REGEXP ? AND wordform NOT IN (?,?,?,?));',
            'values': ['\\bNX0 AX0$', 'AA0 N AX0', 'NN', 'MAS', 'søknader', 'søknadene', 'dugnader', 'dugnadene'],
            'is_constrained': True
        }, {
            'query': 'UPDATE sw_spoken SET nofabet = REGREPLACE(?,?,nofabet) '
                     'WHERE word_id IN (SELECT word_id FROM words_tmp '
                     'WHERE pos = ? AND feats REGEXP ? AND wordform NOT IN (?,?,?,?));',
            'values': [
                '\\bNX0 AX0$', 'AA0 N AX0', 'NN', 'MAS', 'søknader', 'søknadene', 'dugnader', 'dugnadene'
            ],
            'is_constrained': True
        }]]

        # when
        updater_obj._construct_update_queries()
        # then
        assert updater_obj._updates == expected_updates

    @pytest.mark.skip
    def test_update(self):
        assert False

    @pytest.mark.skip
    def test_get_connection(self):
        assert False

    @pytest.mark.skip
    def test_get_results(self):
        assert False

    @pytest.mark.skip
    def test_close_connection(self):
        assert False

################################

# ''' An example of how to mock the sqlite3.connection method '''
#
# from unittest.mock import MagicMock, Mock, patch
# import unittest
# import sqlite3
#
#
# class MyTests(unittest.TestCase):
#
#     def test_sqlite3_connect_success(self):
#         sqlite3.connect = MagicMock(return_value='connection succeeded')
#
#         dbc = DataBaseClass()
#         sqlite3.connect.assert_called_with('test_database')
#         self.assertEqual(dbc.connection, 'connection succeeded')
#
#     def test_sqlite3_connect_fail(self):
#         sqlite3.connect = MagicMock(return_value='connection failed')
#
#         dbc = DataBaseClass()
#         sqlite3.connect.assert_called_with('test_database')
#         self.assertEqual(dbc.connection, 'connection failed')
#
#     def test_sqlite3_connect_with_sideaffect(self):
#         self._setup_mock_sqlite3_connect()
#
#         dbc = DataBaseClass('good_connection_string')
#         self.assertTrue(dbc.connection)
#         sqlite3.connect.assert_called_with('good_connection_string')
#
#         dbc = DataBaseClass('bad_connection_string')
#         self.assertFalse(dbc.connection)
#         sqlite3.connect.assert_called_with('bad_connection_string')
#
#     def _setup_mock_sqlite3_connect(self):
#         values = {'good_connection_string': True,
#                   'bad_connection_string': False}
#
#         def side_effect(arg):
#             return values[arg]
#
#         sqlite3.connect = Mock(side_effect=side_effect)
#
#
# class DataBaseClass():
#
#     def __init__(self, connection_string='test_database'):
#         self.connection = sqlite3.connect(connection_string)

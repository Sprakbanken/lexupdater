"""
Test suite for the lexupdater.py script in the lexupdater package
"""
from unittest.mock import patch

import pytest

import lexupdater


def test_get_base(db_updater_obj):
    # given
    input_connection = db_updater_obj.get_connection()
    # when
    result = lexupdater.get_base(input_connection)
    # then
    assert result is not None
    assert isinstance(result, list)
    assert result != []
    assert result[0] is not None


@pytest.fixture
def dir_path(tmp_path):
    """Temporary test path to an output directory."""
    dir_path = tmp_path / "sub"
    dir_path.mkdir()
    return dir_path


@pytest.mark.parametrize("write_base", [True, False], ids=["base", "no_base"])
def test_main_script_some_dialects(some_dialects, write_base, dir_path):
    # given
    with patch("lexupdater.lexupdater.OUTPUT_DIR", new=dir_path):
        with patch("lexupdater.lexupdater.DatabaseUpdater"):
            # when
            # use the same boolean value for writing the base lexicon, and to
            # select and print words matching the rules
            # (the two conditions don't affect each other)
            lexupdater.main(some_dialects, write_base, match_words=write_base)

            # Ensure we are comparing only filenames, not full paths
            expected_files = [f"{dialect}.txt" for dialect in some_dialects]
            result_files = [file_path.name for file_path in dir_path.iterdir()]
            # then
            assert result_files != []
            for file in result_files:
                assert file.endswith(".txt")
            # dialect files are only written if match_words is False
            assert all(
                [file in result_files for file in expected_files]
            ) != write_base
            assert ("base.txt" in result_files) == write_base

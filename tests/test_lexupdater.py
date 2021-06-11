"""
Test suite for the lexupdater.py script in the lexupdater package
"""
from unittest.mock import patch

import pytest

from lexupdater import lexupdater


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
            expected_update_files = [
                f"updated_lexicon_{dialect}.txt" for dialect in some_dialects
            ]
            expected_match_files = [
                f"words_matching_rules_{dialect}.txt" for dialect in some_dialects
            ]
            result_files = [file_path.name for file_path in dir_path.iterdir()]
            # then
            assert result_files != []
            for file in result_files:
                assert file.endswith(".txt")
            # updated lexicon files are only written if match_words is False
            assert all(
                [file in result_files for file in expected_update_files]
            ) != write_base
            # while matching words files are written if match_words is True
            assert all(
                [file in result_files for file in expected_match_files]
            ) == write_base
            assert ("base.txt" in result_files) == write_base

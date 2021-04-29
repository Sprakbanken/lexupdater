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
    dir_path = tmp_path / "sub"
    dir_path.mkdir()
    return dir_path


@pytest.mark.parametrize("write_base", [True, False], ids=["base", "no_base"])
def test_main_script_some_dialects(
        some_dialects,
        write_base,
        dir_path
):
    # given
    with patch("lexupdater.lexupdater.output_dir", new=dir_path):
        with patch("lexupdater.lexupdater.DatabaseUpdater"):
            # when
            lexupdater.main(some_dialects, write_base)

            # Ensure we are comparing only filenames, not full paths
            expected_files = [f"{d}.txt" for d in some_dialects]
            result_files = [file_path.name for file_path in dir_path.iterdir()]
            # then
            assert all([
                file in result_files for file in expected_files
            ]), print(result_files)
            assert ("base.txt" in result_files) == write_base



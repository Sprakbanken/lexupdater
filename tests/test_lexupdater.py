"""
Test suite for the lexupdater.py script in the lexupdater package
"""

import pytest
from click.testing import CliRunner

from lexupdater import lexupdater


def test_main_default_update(all_dialects, tmp_path):
    # given
    # specify output directory
    output_dir = (tmp_path / "output")
    output_dir.mkdir()
    # Compare only filenames, not full paths
    expected_update_files = [
        f"updated_lexicon_{dialect}.txt" for dialect in all_dialects
    ]
    runner = CliRunner()
    # when
    # Use default values, except database and output directory
    result = runner.invoke(
        lexupdater.main,
        f"-o {str(output_dir)} --db tests/dummy_data.db"
    )
    result_files = [
        file_path.name for file_path in output_dir.iterdir()
    ]
    # then
    assert result.exit_code == 0
    assert result_files != []
    for file in result_files:
        assert file.endswith(".txt")
    assert all([file in result_files for file in expected_update_files])


@pytest.mark.parametrize(
    "cli_arg,expected_files",
    [
        ["-b", ("base.txt", "updated_lexicon_n_written.txt")],
        ["-m", ("words_matching_rules_n_written.txt",)],
    ],
    ids=["base", "match"]
)
def test_script_with_config_and_cli_args(cli_arg, expected_files, tmp_path):
    # given
    output_dir = (tmp_path / "dummy_output")
    output_dir.mkdir()
    assert output_dir.exists()
    runner = CliRunner()
    # when
    result = runner.invoke(
        lexupdater.main,
        f"{cli_arg} -v -c tests/dummy_config.py -o {output_dir}"
    )
    result_files = [file_path.name for file_path in output_dir.iterdir()]
    # then
    assert result.exit_code == 0
    assert all([file in result_files for file in expected_files])

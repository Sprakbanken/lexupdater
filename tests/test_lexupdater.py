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
        f"-o {str(output_dir)} -db tests/dummy_data.db"
    )
    result_files = [
        file_path.name for file_path in output_dir.iterdir()
    ]
    # then
    assert result.exit_code == 0
    assert result_files != []
    assert all([file in result_files for file in expected_update_files])


@pytest.mark.parametrize(
    "sub_command,expected_file",
    [
        ["base", "base.txt"],
        ["match", "words_matching_rules_n_written.txt"],
        ["insert", "base_new_words.txt"],
        ["update", "updated_lexicon_n_written.txt"],
    ]
)
def test_subcommands(sub_command, expected_file, tmp_path):
    # given
    output_dir = (tmp_path / "dummy_output")
    output_dir.mkdir()
    assert output_dir.exists()
    runner = CliRunner()
    # when
    result = runner.invoke(
        lexupdater.main,
        f"-c tests/dummy_config.py -o {str(output_dir)} {sub_command}"
    )
    result_files = [file_path.name for file_path in output_dir.iterdir()]
    # then
    assert result.exit_code == 0
    assert expected_file in result_files


def test_convert_formats(tmp_path):
    output_dir = (tmp_path / "dummy_output")
    output_dir.mkdir()

    (output_dir / "updated_lexicon_n_written.txt").write_text(
        "-elser	NN	PLU|IND|NOM|NEU-MAS-FEM	EH1 L S AA0 R")
    expected_file = "NB_nob_n.dict"
    runner = CliRunner()
    # when
    result = runner.invoke(
        lexupdater.main,
        f"-c tests/dummy_config.py convert -l {str(output_dir)}"
    )
    result_files = [file_path.name for file_path in output_dir.iterdir()]
    # then
    assert result.exit_code == 0
    assert expected_file in result_files


def test_compare_command(tmp_path):
    output_dir = (tmp_path / "dummy_output")
    output_dir.mkdir()
    runner = CliRunner()
    # when
    result = runner.invoke(
        lexupdater.main,
        f"-c tests/dummy_config.py compare -o {str(output_dir)}"
    )
    expected_files = list(output_dir.glob("comparison_*.txt"))
    result_files = list(output_dir.iterdir())
    # then
    assert result.exit_code == 0
    assert [f in result_files for f in expected_files]

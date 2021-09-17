"""Test suite for helper functions in utils.py."""
import re
from pathlib import Path
from typing import Generator

import pandas as pd
import pytest

from lexupdater.constants import ruleset_schema, exemption_schema, \
    dialect_schema
from lexupdater import utils


def test_write_lexicon(tmp_path):
    # given
    output_file = tmp_path / "some_file.txt"
    out_data = [["hello", "world", "this"], ["is", "a", "test"]]
    # when
    utils.write_lexicon(output_file, out_data)
    # then
    assert output_file.exists()
    assert output_file.read_text() == 'hello\tworld\tthis\nis\ta\ttest\n'


def test_flatten_match_results():
    # given
    words = [
        ("one", "line", "of db data"),
        ("another", "line", "of data")
    ]
    nested_structure = [
        ("nofabet regex pattern", words)
    ]
    expected = [
        ["nofabet regex pattern", "one", "line", "of db data"],
        ["nofabet regex pattern", "another", "line", "of data"]
    ]
    # when
    result = utils.flatten_match_results(nested_structure)
    # then
    assert isinstance(result, Generator)
    result_list = list(result)
    assert len(expected) == len(result_list)
    for result_element, expected_element in zip(result_list, expected):
        assert result_element == expected_element


def test_filter_list_by_list_all_valid(some_dialects, all_dialects):
    # given
    input_dialects = some_dialects + ["e_spoken"]
    # when
    result = utils.filter_list_by_list(input_dialects, all_dialects)
    # then
    assert result == input_dialects


def test_filter_list_by_list_not_valid(some_dialects, all_dialects):
    # given
    input_dialects = some_dialects + ["bergensk"]
    # when
    result = utils.filter_list_by_list(input_dialects, all_dialects)
    # then
    assert result == some_dialects


@pytest.fixture
def module_file_path(tmp_path):
    """Create a python file with dummy variables, and return the path."""
    file_path = (tmp_path / "dummy_module.py")
    module_content = """DATABASE = "a_database.db"
    OUTPUT_DIR = "delete_this_folder"
    RULES_FILE = "some_rules.py"
    EXEMPTIONS_FILE = "and_some_exemptions.py"
    NEWWORD_FILE = "all_brand_new_newwords.py"
    DIALECTS = [
        "norwegian_dialect",
    ]
    """
    file_path.write_text(module_content.replace(r"    ", ""))
    return str(file_path)


def test_load_module_from_path(module_file_path):
    # when
    result_module = utils.load_module_from_path(module_file_path)
    # then
    assert result_module.DATABASE == "a_database.db"
    assert result_module.OUTPUT_DIR == "delete_this_folder"
    assert result_module.RULES_FILE == "some_rules.py"
    assert result_module.EXEMPTIONS_FILE == "and_some_exemptions.py"
    assert result_module.NEWWORD_FILE == "all_brand_new_newwords.py"
    assert len(result_module.DIALECTS) == 1
    assert result_module.DIALECTS == ["norwegian_dialect"]


def test_load_module_from_path_raises_error():
    file_path = "wrong_path_extension.txt"
    # given
    with pytest.raises(AssertionError):
        # when
        utils.load_module_from_path(file_path)


def test_load_vars_from_module():
    # given
    import dummy_config
    # when
    result = utils.load_vars_from_module(dummy_config)
    # then
    assert isinstance(result, list)
    assert "tests/dummy_data.db" in result
    assert "tests/delete_me" in result
    assert "tests/dummy_rules.py" in result
    assert "tests/dummy_exemptions.py" in result
    assert ["n_written"] in result


def test_load_data(module_file_path):
    # when
    result = utils.load_data(module_file_path)
    # then
    # verify the same as for load_vars_from_module, but different values
    assert isinstance(result, list)
    assert "a_database.db" in result
    assert "delete_this_folder" in result
    assert "some_rules.py" in result
    assert "and_some_exemptions.py" in result
    assert "all_brand_new_newwords.py" in result
    assert ["norwegian_dialect"] in result


def test_load_data_raises_error():
    file_path = "wrong_path.txt"
    # given
    with pytest.raises(AssertionError):
        # when
        utils.load_data(file_path)


@pytest.mark.parametrize(
    "paths,col_names",
    [
        (["tests/dummy_newwords_2.csv"], ["token"]),
        (
            ["tests/dummy_newwords_1.csv", "tests/dummy_newwords_2.csv"],
            [
                "token",
                "transcription",
                "alt_transcription_1",
                "alt_transcription_2",
                "alt_transcription_3",
                "pos",
                "morphology"
            ]
        ),
        (["tests/dummy_newwords_2.csv"], ["word", "transcription", "feats"])
    ],
    ids=["minimal_input", "maximal_input", "wrong_input"]
)
def test_load_newwords(paths, col_names):
    # given
    valid_col_names = [
        "token",
        "transcription",
        "alt_transcription_1",
        "alt_transcription_2",
        "alt_transcription_3",
        "pos",
        "morphology"
    ]
    result = utils.load_newwords(paths, col_names)[:5]

    assert isinstance(result, pd.DataFrame)
    assert all([col in valid_col_names for col in result.columns])


def test_validate_objects(ruleset_list, some_dialects, exemptions_list):
    # given
    mixed_rules = ruleset_list + ["invalid_ruleset"]
    mixed_exemptions = exemptions_list + ["invalid_exemption"]
    mixed_dialects = some_dialects + ["invalid_dialect"]
    # when
    result_rules = utils.validate_objects(mixed_rules, ruleset_schema)
    result_exemptions = utils.validate_objects(mixed_exemptions,
                                               exemption_schema)
    result_dialects = utils.validate_objects(mixed_dialects, dialect_schema)
    # then
    assert result_rules == ruleset_list
    assert result_exemptions == exemptions_list
    assert result_dialects == some_dialects


def test_matching_data_to_dict():
    # given
    test_entries = [("pattern_str", [("word_str","transcription","pron_id")])]
    expected = {
        "pattern": ("pattern_str",),
        "word": ("word_str",),
        "transcription": ("transcription",),
        "pron_id": ("pron_id",),
    }
    # when
    result = utils.matching_data_to_dict(test_entries)
    # then
    assert str(result) == str(expected)


@pytest.mark.parametrize(
    "filter_ids,test_entries,expected",
    [
        [None,
         (("w1","p1","f1","t1"),("w2","p2","f2","t2")),
         {
             "word": ("w1", "w2"),
             "pos": ("p1", "p2"),
             "feats": ("f1", "f2"),
             "new_transcription": ("t1", "t2"),
         }],
        [None,
         (("u1","w1","p1","f1","t1","pr1"),("u2","w2","p2","f2","t2","pr2")),
         {
            "unique_id": ("u1", "u2"),
            "word": ("w1", "w2"),
            "pos": ("p1", "p2"),
            "feats": ("f1", "f2"),
            "new_transcription": ("t1", "t2"),
            "pron_id": ("pr1", "pr2"),
         }
        ],
        [[1,2,3],
         (("u1","w1","p1","f1","t1",1),("u2","w2","p2","f2","t2","pr2")),
         {
            "unique_id": ["u1"],
            "word": ["w1"],
            "pos": ["p1"],
            "feats": ["f1"],
            "new_transcription": ["t1"],
            "pron_id": [1],
         }]
    ]
)
def test_updated_data_to_dict(filter_ids, test_entries,expected):
    # when
    result = utils.updated_data_to_dict(
        test_entries, ids_to_filter_by=filter_ids)
    # then
    assert isinstance(result, dict)
    assert str(result) == str(expected)


@pytest.mark.parametrize(
    "update_bool,filter_ids,expected",
    [
        (False,
         [1,2],
         pd.DataFrame({
             "dialect": ["dialect_name", "dialect_name"],
             "unique_id": ["u1","u2"],
             "word": ["w1","w2"],
             "pos": ["p1","p2"],
             "feats": ["f1", "f2"],
             "new_transcription": ["t1","t2"],
             "pron_id": [1, 2],
         })),
        (True,
         None,
         pd.DataFrame({
             "dialect": ["dialect_name", "dialect_name", "dialect_name"],
             "unique_id": ["u1","u2", "u4"],
             "word": ["w1","w2", "w4"],
             "pos": ["p1","p2", "p4"],
             "feats": ["f1", "f2", "f4"],
             "new_transcription": ["t1","t2", "t4"],
             "pron_id": [1, 2, 4],
         }))
    ]
)
def test_data_to_df_update(update_bool, filter_ids, expected):
    # given
    test_data = {"dialect_name": (
        ("u1", "w1", "p1", "f1", "t1", 1),
        ("u2", "w2", "p2", "f2", "t2", 2),
        ("u4", "w4", "p4", "f4", "t4", 4))}
    input_pron_ids = {1, 2, 4}
    # when
    result = utils.data_to_df(
        test_data, update=update_bool, pron_ids=filter_ids)
    # then
    assert isinstance(result, pd.DataFrame)
    assert len(result.index) == len(expected.index)
    assert all([c in result.columns for c in expected.columns])
    assert input_pron_ids.issuperset(set(result.pron_id))


def test_data_to_df_matching():
    # given
    test_data = {"dialect_name": [
        ("pattern_str", [("word_str", "transcription_str", "pron_id_str")])
    ]}
    # when
    result = utils.data_to_df(test_data)
    result_values = result.iloc[0].values
    # then
    assert isinstance(result, pd.DataFrame)
    assert len(result.columns) == 5
    assert len(result.index) == 1
    assert "dialect_name" in result_values
    assert "pattern_str" in result_values
    assert "word_str" in result_values
    assert "transcription_str" in result_values
    assert "pron_id_str" in result_values


def test_compare_transcriptions(db_updater_obj):
    test_data_updated = {"dialect_name": (
        ("u1", "w1", "p1", "f1", "t1", 1),
        ("u2", "w2", "p2", "f2", "t2", 2),
        ("u4", "w4", "p4", "f4", "t4", 4))}
    test_data_matching = {"dialect_name": [
        ("pattern_str", [("word_str", "transcription_str", "pron_id_str")]),
        ("pattern_str", [("w1", "t1", 1)])
    ]}
    # when
    result = utils.compare_transcriptions(test_data_matching, test_data_updated)
    # then
    assert isinstance(result, pd.DataFrame)
    assert len(result.index) == 1


def test_format_rulesets_and_exemptions(ruleset_fixture):
    # given
    expected_rule = (
        "\n"
        "test_rule_set = {'name': 'test_rule_set',\n"
        "                 'areas': ['e_spoken'],\n"
        "                 'rules': "  # there is no newline in the string here
        "[{'pattern': 'transcription_pattern_to_replace',\n"
        "                            'replacement': 'D DH \\\\1 EE1',\n"
        "                            'constraints': [{'field': 'pos',\n"
        "                                             'pattern': 'value',\n"
        "                                             'is_regex': True}]}]}\n")

    expected_exemption = re.compile(
        r"\nexemption_(\d+_\d+) = {(\s+)'ruleset': 'test_rule_set',(\s+)"
        r"'words': \['exempt_word']}\n")
    # when
    rule_result, exemption_result = utils.format_rulesets_and_exemptions(
        [ruleset_fixture]
    )
    # then
    assert rule_result == expected_rule
    exemption_match = re.match(expected_exemption, exemption_result)
    assert exemption_match is not None


@pytest.fixture
def lexicon_dir_prefixes(tmp_path):
    lex_dir = tmp_path / "lexica"
    lex_dir.mkdir()
    in_prefix = "lexupdater"
    out_prefix = "mfa"
    file_content = re.sub("\n        ", "\n", """
        -abel	JJ	SIN|IND|NOM|MAS-FEM|POS	AA1 B AX0 L
        -abels	JJ	SIN|IND|GEN|MAS-FEM|POS	AA1 B AX0 L S
        -abelt	JJ	SIN|IND|NOM|NEU|POS	AA1 B AX0 L T
        -abelts	JJ	SIN|IND|GEN|NEU|POS	AA1 B AX0 L T S
        -able	JJ	SIN-PLU|DEF|NOM||POS	AA1 B L AX0
        -ables	JJ	SIN-PLU|DEF|GEN||POS	AA1 B L AX0 S
        """).lstrip()
    for suffix in ("spoken","written"):
        lex_file = lex_dir / f"{in_prefix}_dialect_{suffix}.txt"
        lex_file.write_text(file_content)
    return lex_dir, in_prefix, out_prefix


@pytest.mark.parametrize(
    "combine_files,expected_filenames,expected_content,probabilities",
    [
        (False, ["dialect_spoken.dict", "dialect_written.dict"], """
-abel AA1 B AX0 L
-abels AA1 B AX0 L S
-abelt AA1 B AX0 L T
-abelts AA1 B AX0 L T S
-able AA1 B L AX0
-ables AA1 B L AX0 S
""".lstrip(), {}),
        (True, ["dialect.dict"], """
-abel 0.8 AA1 B AX0 L
-abel 0.4 AA1 B AX0 L
-abels 0.8 AA1 B AX0 L S
-abels 0.4 AA1 B AX0 L S
-abelt 0.8 AA1 B AX0 L T
-abelt 0.4 AA1 B AX0 L T
-abelts 0.8 AA1 B AX0 L T S
-abelts 0.4 AA1 B AX0 L T S
-able 0.8 AA1 B L AX0
-able 0.4 AA1 B L AX0
-ables 0.8 AA1 B L AX0 S
-ables 0.4 AA1 B L AX0 S
""".lstrip(),
         dict(spoken=0.8, written=0.4)),
    ],
    ids=["individual", "combined"]
)
def test_convert_lex_to_mfa(
        lexicon_dir_prefixes, combine_files, expected_filenames,
        expected_content, probabilities):
    """Test conversion of multiple files in a directory."""
    # given
    lex_dir, in_prefix, out_prefix = lexicon_dir_prefixes
    # when
    utils.convert_lex_to_mfa(
        lex_dir=lex_dir,
        dialects=["dialect_spoken", "dialect_written"],
        in_file_prefix=in_prefix,
        out_file_prefix=out_prefix,
        combine_dialect_forms=combine_files,
        probabilities=probabilities
    )
    # then
    result = list(lex_dir.glob(f"{out_prefix}_*.dict"))
    expected = [f"{out_prefix}_{f_name}" for f_name in expected_filenames]
    for filename in result:
        assert filename.name in expected
        assert filename.read_text() == expected_content


@pytest.mark.parametrize(
    "pron_prob,expected",
    [
        (None, [
            '-abel AA1 B AX0 L\n',
            '-abels AA1 B AX0 L S\n',
            '-abelt AA1 B AX0 L T\n',
            '-abelts AA1 B AX0 L T S\n',
            '-able AA1 B L AX0\n',
            '-ables AA1 B L AX0 S\n'
        ]),
        (0.8, [
            '-abel 0.8 AA1 B AX0 L\n',
            '-abels 0.8 AA1 B AX0 L S\n',
            '-abelt 0.8 AA1 B AX0 L T\n',
            '-abelts 0.8 AA1 B AX0 L T S\n',
            '-able 0.8 AA1 B L AX0\n',
            '-ables 0.8 AA1 B L AX0 S\n'
        ])
    ],
    ids=["no_weighted_prons", "weighted_pronunciations"]
)
def test_format_mfa_dict(
        lexicon_dir_prefixes, pron_prob, expected):
    """Test conversion of two files merged into one, with probabilities."""
    # given
    lex_dir, in_prefix, out_prefix = lexicon_dir_prefixes
    lex_file = Path(lex_dir / f"{in_prefix}_dialect_spoken.txt")
    with open(lex_file) as fp:
        lexicon = fp.readlines()
    # when
    result = utils.format_mfa_dict(lexicon, prob=pron_prob)
    # then
    assert len(expected) == len(result)
    assert all([e_line == r_line for e_line, r_line in zip(expected,
                                                           result)]), result


def test_ensure_path_exists(tmp_path):
    input_path = tmp_path / "new_folder"
    utils.ensure_path_exists(input_path)
    assert input_path.exists()

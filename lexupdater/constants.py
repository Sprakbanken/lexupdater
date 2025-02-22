"""Constant values used by lexupdater.

* Validation schemas for the configurable input rules, exemptions and dialects.
* SQL query template strings to create tables, insert values, update entries
and select entries.
"""
import logging
import re

import pandera as pa
from pandera import Column, DataFrameSchema, Check
from schema import Schema, Optional

# Licit NoFAbet phones
LICIT_PHONES = [
    "AA0",
    "AA1",
    "AA2",
    "AA3",
    "AE0",
    "AE1",
    "AE2",
    "AE3",
    "AEH0",
    "AEH1",
    "AEH2",
    "AEH3",
    "AEJ0",
    "AEJ1",
    "AEJ2",
    "AEJ3",
    "AEW0",
    "AEW1",
    "AEW2",
    "AEW3",
    "AH0",
    "AH1",
    "AH2",
    "AH3",
    "AJ0",
    "AJ1",
    "AJ2",
    "AJ3",
    "AX0",
    "AX1",
    "AX2",
    "AX3",
    "B",
    "D",
    "DH",
    "DJ",
    "EE0",
    "EE1",
    "EE2",
    "EE3",
    "EH0",
    "EH1",
    "EH2",
    "EH3",
    "EXH",
    "F",
    "G",
    "H",
    "IH0",
    "IH1",
    "IH2",
    "IH3",
    "II0",
    "II1",
    "II2",
    "II3",
    "INH",
    "J",
    "JX0",
    "JX1",
    "JX2",
    "JX3",
    "K",
    "KJ",
    "L",
    "LG",
    "LX0",
    "LX1",
    "LX2",
    "LX3",
    "M",
    "MX0",
    "MX1",
    "MX2",
    "MX3",
    "N",
    "NG",
    "NHES",
    "NX0",
    "NX1",
    "NX2",
    "NX3",
    "OA0",
    "OA1",
    "OA2",
    "OA3",
    "OAH0",
    "OAH1",
    "OAH2",
    "OAH3",
    "OE0",
    "OE1",
    "OE2",
    "OE3",
    "OEH0",
    "OEH1",
    "OEH2",
    "OEH3",
    "OEJ0",
    "OEJ1",
    "OEJ2",
    "OEJ3",
    "OH0",
    "OH1",
    "OH2",
    "OH3",
    "OJ0",
    "OJ1",
    "OJ2",
    "OJ3",
    "OAJ0",
    "OAJ1",
    "OAJ2",
    "OAJ3",
    "OO0",
    "OO1",
    "OO2",
    "OO3",
    "OU0",
    "OU1",
    "OU2",
    "OU3",
    "P",
    "R",
    "RD",
    "RL",
    "RLX0",
    "RLX1",
    "RLX2",
    "RLX3",
    "RN",
    "RNX0",
    "RNX1",
    "RNX2",
    "RNX3",
    "RT",
    "RX0",
    "RX1",
    "RX2",
    "RX3",
    "S",
    "SJ",
    "SX0",
    "SX1",
    "SX2",
    "SX3",
    "T",
    "TH",
    "TSJ",
    "UH0",
    "UH1",
    "UH2",
    "UH3",
    "UU0",
    "UU1",
    "UU2",
    "UU3",
    "UX1",
    "UX2",
    "UX3",
    "V",
    "VHES",
    "VX0",
    "VX1",
    "VX2",
    "VX3",
    "W",
    "X",
    "YH0",
    "YH1",
    "YH2",
    "YH3",
    "YY0",
    "YY1",
    "YY2",
    "YY3",
    "Z",
    "RS",
    "_",
]

# Define validation Schemas
dialect_schema = Schema(
    [
        "e_spoken",
        "e_written",
        "sw_spoken",
        "sw_written",
        "w_spoken",
        "w_written",
        "t_spoken",
        "t_written",
        "n_spoken",
        "n_written",
    ]
)

constraint_schema = Schema({"field": str, "pattern": str, "is_regex": bool})


def _backreference_check(string):
    regex_match = re.match(r"(?P<back_ref>\\\d)|(?P<phoneme>\w{1,3})", string)
    if regex_match is None:
        return False
    phoneme = regex_match.group("phoneme")
    if (phoneme is not None) and (phoneme in LICIT_PHONES):
        return True
    back_ref = regex_match.group("back_ref")
    if back_ref is not None:
        return True
    return False


rule_schema = Schema(
    {
        "pattern": str,
        "replacement": str,
        "constraints": [Optional(constraint_schema.schema)],
    }
)


ruleset_schema = Schema(
    {
        "areas": dialect_schema.schema,
        "name": str,
        "rules": [rule_schema.schema],
    }
)


exemption_schema = Schema({"ruleset": str, "words": list})


def phone_is_valid(p):
    if not (validation := p in LICIT_PHONES):
        logging.error("Phoneme '%s' is invalid.", p)
    return validation


def phone_check(s: str):
    return (
        all(phone_is_valid(ph) for ph in s.split(" "))
        if isinstance(s, str) else True
    )

check_phones = Check(
    phone_check,
    element_wise=True
)


newword_schema = DataFrameSchema(
    {
        "token": Column(pa.String),
        "transcription": Column(pa.String, check_phones),
        "alt_transcription_1": Column(pa.String, check_phones, nullable=True),
        "alt_transcription_2": Column(pa.String, check_phones, nullable=True),
        "alt_transcription_3": Column(pa.String, check_phones, nullable=True),
        "pos": Column(pa.String),
        "morphology": Column(pa.String, nullable=True),
        "update_info": Column(pa.String, required=False, nullable=True),
    }
)


newword_column_names = [
    "token",
    "transcription",
    "alt_transcription_1",
    "alt_transcription_2",
    "alt_transcription_3",
    "pos",
    "morphology",
    "update_info"
]


LEX_PREFIX = "updated_lexicon"
MATCH_PREFIX = "words_matching_rules"
MFA_PREFIX = "NB_nob"
NEW_PREFIX = "base_new_words"
CHANGE_PREFIX = "tracked_update"


# Define SQL query templates
CREATE_PRON_TABLE_STMT = """CREATE TEMPORARY TABLE {pron_table_name} (
pron_id INTEGER PRIMARY KEY AUTOINCREMENT,
nofabet TEXT NOT NULL,
certainty INTEGER NOT NULL,
unique_id VARCHAR NOT NULL,
FOREIGN KEY(unique_id) REFERENCES words(unique_id)
ON UPDATE CASCADE);
"""


CREATE_WORD_TABLE_STMT = """CREATE TEMPORARY TABLE {word_table_name} (
word_id INTEGER PRIMARY KEY AUTOINCREMENT,
wordform TEXT NOT NULL,
pos TEXT NOT NULL,
feats TEXT NOT NULL,
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
update_info TEXT,
lang_code TEXT,
expansion TEXT,
set_id TEXT,
lemma TEXT,
sem_code TEXT,
frequency TEXT,
orig_wf TEXT,
comment TEXT,
unique_id VARCHAR NOT NULL UNIQUE
);"""


INSERT_STMT = "INSERT INTO {table_name} SELECT * FROM {other_table};"


WHERE_WORD_IN_STMT = (
    "WHERE unique_id IN (SELECT w.unique_id FROM {word_table} w WHERE {conditions})"
)


WHERE_REGEXP = "WHERE REGEXP(?,nofabet)"

COL_WORDFORM = "w.wordform"
COL_pUID = "p.unique_id"
COL_UID = "p.unique_id"
COL_PRON = "p.nofabet"
COL_PRONID = "p.pron_id"
COL_POS = "w.pos"
COL_FEATS = "w.feats"
COL_INFO = "w.update_info"


LEXICON_COLUMNS = ", ".join([COL_WORDFORM, COL_POS, COL_FEATS, COL_UID, COL_INFO, COL_PRON])


COLMAP = {
    'unique_id': 'wordform_id',
    'nofabet': 'nofabet_transcription',
    'ipa': 'ipa_transcription',
    'sampa': 'sampa_transcription'
}


UPDATE_QUERY = (
    "UPDATE {dialect} SET nofabet = REGREPLACE(?,?,nofabet) {where_word_in_stmt};"
)


SELECT_QUERY = (
    "SELECT "
    "{columns} "
    "FROM {word_table} w "
    "LEFT JOIN {pron_table} p "
    "ON p.unique_id = w.unique_id "
    "{where_regex} "
    "{where_word_in_stmt};"
)


UNIQUE_ID_PATTERN = "NB{counter}"


NEWWORD_INSERT = "INSERT INTO {table} ({columns}) VALUES ({vars});"


NW_WORD_COLS = ("wordform, pos, feats, unique_id, update_info", "?,?,?,?,?")


NW_PRON_COLS = ("nofabet, unique_id, certainty", "?,?,?")

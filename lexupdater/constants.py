"""Constant values used by lexupdater.

* Validation schemas for the configurable input rules, exemptions and dialects.
* SQL query template strings to create tables, insert values, update entries
and select entries.
"""

import pandera as pa
from pandera import Column, DataFrameSchema, Check
from schema import Schema, Optional

# Licit NoFAbet phones
LICIT_PHONES = [
    "AA0", "AA1", "AA2", "AA3", "AE0", "AE1", "AE2", "AE3",
    "AEH0", "AEH1", "AEH2", "AEH3", "AEJ0", "AEJ1", "AEJ2",
    "AEJ3", "AEW0", "AEW1", "AEW2", "AEW3", "AH0", "AH1", "AH2",
    "AH3", "AJ0", "AJ1", "AJ2", "AJ3", "AX0", "AX1", "AX2", "AX3",
    "B", "D", "DH", "DJ", "EE0", "EE1", "EE2", "EE3", "EH0",
    "EH1", "EH2", "EH3", "EXH", "F", "G", "H", "IH0", "IH1",
    "IH2", "IH3", "II0", "II1", "II2", "II3", "INH", "J", "JX0",
    "JX1", "JX2", "JX3", "K", "KJ", "L", "LG", "LX0", "LX1", "LX2",
    "LX3", "M", "MX0", "MX1", "MX2", "MX3", "N", "NG", "NHES",
    "NX0", "NX1", "NX2", "NX3", "OA0", "OA1", "OA2", "OA3",
    "OAH0", "OAH1", "OAH2", "OAH3", "OE0", "OE1", "OE2", "OE3",
    "OEH0", "OEH1", "OEH2", "OEH3", "OEJ0", "OEJ1", "OEJ2", "OEJ3",
    "OH0", "OH1", "OH2", "OH3", "OJ0", "OJ1", "OJ2", "OJ3", "OO0",
    "OO1", "OO2", "OO3", "OU0", "OU1", "OU2", "OU3", "P", "R",
    "RD", "RL", "RLX0", "RLX1", "RLX2", "RLX3", "RN", "RNX0", "RNX1",
    "RNX2", "RNX3", "RT", "RX0", "RX1", "RX2", "RX3", "S", "SJ",
    "SX0", "SX1", "SX2", "SX3", "T", "TH", "TSJ", "UH0", "UH1",
    "UH2", "UH3", "UU0", "UU1", "UU2", "UU3", "UX1", "UX2", "UX3",
    "V", "VHES", "VX0", "VX1", "VX2", "VX3", "W", "X", "YH0",
    "YH1", "YH2", "YH3", "YY0", "YY1", "YY2", "YY3", "Z", "RS"
]

# Define validation Schemas
dialect_schema = Schema([
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
])

constraint_schema = Schema({
    "field": str,
    "pattern": str,
    "is_regex": bool
})

rule_schema = Schema({
    "pattern": str,
    "replacement": str,
    "constraints": [Optional(constraint_schema.schema)],
})

ruleset_schema = Schema({
    "areas": dialect_schema.schema,
    "name": str,
    "rules": [rule_schema.schema],
})

exemption_schema = Schema({"ruleset": str, "words": list})

_phone_check = lambda s: all(
    x in LICIT_PHONES for x in s.split(" ")
) if isinstance(s, str) else True

newword_schema = DataFrameSchema({
    "token": Column(pa.String),
    "transcription": Column(
        pa.String, Check(_phone_check, element_wise=True)
    ),
    "alt_transcription_1": Column(
        pa.String, Check(_phone_check, element_wise=True),
        nullable=True
    ),
    "alt_transcription_2": Column(
        pa.String, Check(_phone_check, element_wise=True),
        nullable=True
    ),
    "alt_transcription_3": Column(
        pa.String, Check(_phone_check, element_wise=True),
        nullable=True
    ),
    "pos": Column(pa.String),
    "morphology": Column(pa.String, nullable=True)
})

newword_column_names = [
        "token",
        "transcription",
        "alt_transcription_1",
        "alt_transcription_2",
        "alt_transcription_3",
        "pos",
        "morphology"
    ]

LEX_PREFIX="updated_lexicon"
MATCH_PREFIX="words_matching_rules"
MFA_PREFIX="NST_nob"

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
    "WHERE unique_id IN (SELECT w.unique_id FROM {word_table} w "
    "WHERE {conditions})"
)

WHERE_REGEXP = "WHERE REGEXP(?,nofabet)"

WORD_NOT_IN = "w.wordform NOT IN"

COL_WORD_PRON_ID = "w.wordform, p.nofabet, p.pron_id "

COL_ID_WORD_FEATS_PRON_ID = (
    "w.unique_id, w.wordform, w.pos, w.feats, p.nofabet, p.pron_id "
)

COL_WORD_POS_FEATS_PRON = "w.wordform, w.pos, w.feats, p.nofabet"

COL_ALL = (
    "w.word_id, "
    "w.wordform, "
    "w.pos, "
    "w.feats, "
    "w.source, "
    "w.decomp_ort, "
    "w.decomp_pos, "
    "w.garbage, "
    "w.domain, "
    "w.abbr, "
    "w.set_name, "
    "w.style_status, "
    "w.inflector_role, "
    "w.inflector_rule, "
    "w.morph_label, "
    "w.compounder_code, "
    "w.update_info, "
    "w.lang_code, "
    "w.expansion, "
    "w.set_id, "
    "w.lemma, "
    "w.sem_code, "
    "w.frequency, "
    "w.orig_wf, "
    "w.comment, "
    "p.pron_id, "
    "p.nofabet, "
    "p.certainty, "
    "p.unique_id "
)

UPDATE_QUERY = (
    "UPDATE {dialect} SET nofabet = REGREPLACE(?,?,nofabet) "
    "{where_word_in_stmt};"
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

NEWWORD_INSERT = (
    "INSERT INTO {table} ({columns}) "
    "VALUES ({vars});"
)

NW_WORD_COLS = (
    "wordform, pos, feats, unique_id",
    "?,?,?,?")

NW_PRON_COLS = (
    "nofabet, unique_id, certainty",
    "?,?,?"
)

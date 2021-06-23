"""Constant values used by lexupdater.

* Validation schemas for the configurable input rules, exemptions and dialects.
* SQL query template strings to create tables, insert values, update entries
and select entries.
"""
from schema import Schema, Optional
import pandera as pa
from pandera import Column, DataFrameSchema 

from config import DIALECTS

dialect_schema = Schema(DIALECTS)

constraint_schema = Schema({
    "field": str,
    "pattern": str,
    "is_regex": bool
})

rule_schema = Schema({
    "pattern": str,
    "repl": str,
    "constraints": [Optional(constraint_schema.schema)],
})

ruleset_schema = Schema({
    "areas": dialect_schema.schema,
    "name": str,
    "rules": [rule_schema.schema],
})


exemption_schema = Schema([{"ruleset": str, "words": list}])

newword_schema = DataFrameSchema({
    "token": Column(pa.String),
    "transcription": Column(pa.String), #TODO: add pa.Check
    "alt_transcription_1": Column(pa.String, required=False),
    "alt_transcription_2": Column(pa.String, required=False),
    "alt_transcription_3": Column(pa.String, required=False),
    "pos": Column(pa.String),
    "morphology": Column(pa.String, required=False)
})

CREATE_PRON_TABLE_STMT = """CREATE TEMPORARY TABLE {pron_table_name} (
pron_id INTEGER NOT NULL,
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

COL_WORD_PRON = "w.wordform, p.nofabet "

COL_ID_WORD_FEATS_PRON = (
    "w.unique_id, w.wordform, w.pos, w.feats, p.nofabet"
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

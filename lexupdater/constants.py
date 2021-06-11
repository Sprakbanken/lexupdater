"""Constant values used by lexupdater.

* Load config values into python structures
* Validation schemas for the configurable input rules, exemptions and dialects.
* SQL query template strings to create tables, insert values, update entries
and select entries.
"""
from pathlib import Path
from runpy import run_path

from schema import Schema, Optional

from . import config


# Load values from config "pointers" into python data structures
DATABASE = Path(config.DATABASE)
OUTPUT_DIR = Path(config.OUTPUT_DIR)

RULES = run_path(config.RULES_FILE).get("ruleset_list")
EXEMPTIONS = run_path(config.EXEMPTIONS_FILE).get("exemptions_list")

WORD_TABLE = config.WORD_TABLE

DIALECTS = config.DIALECTS

# Ensure the output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Define validation Schemas
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


# Define SQL query templates
CREATE_DIALECT_TABLE_STMT = """CREATE TEMPORARY TABLE {dialect} (
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
unique_id VARCHAR NOT NULL
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

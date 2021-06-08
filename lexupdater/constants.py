"""Constant values used by lexupdater.

* Validation schemas for the configurable input rules, exemptions and dialects.
* SQL query template strings to create tables, insert values, update entries
and select entries.
"""
from schema import Schema, Optional

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

CREATE_DIALECT_TABLE_STMT = """CREATE TEMPORARY TABLE {dialect} (
pron_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
pron_id INTEGER NOT NULL,
word_id INTEGER NOT NULL,
nofabet TEXT NOT NULL,
certainty INTEGER NOT NULL,
FOREIGN KEY(word_id) REFERENCES words(word_id)
ON UPDATE CASCADE);
"""

CREATE_WORD_TABLE_STMT = """CREATE TEMPORARY TABLE {word_table_name} (
word_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
word_id INTEGER NOT NULL,
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
update_info TEXT);"""

INSERT_STMT = "INSERT INTO {table_name} SELECT * FROM {other_table};"

UPDATE_QUERY = (
    "UPDATE {dialect} SET nofabet = REGREPLACE(?,?,nofabet) "
    "{where_word_in_stmt};"
)

WHERE_WORD_IN_STMT = (
    "WHERE word_id IN (SELECT w.word_id FROM {word_table} w "
    "WHERE {conditions})"
)

WORD_NOT_IN = "w.wordform NOT IN"

SELECT_WORDS_QUERY = (
        "SELECT w.wordform, p.nofabet "
        "FROM {word_table} w "
        "LEFT JOIN {dialect} p ON p.word_id = w.word_id "
        "WHERE REGEXP(?,nofabet) "
        "{where_word_in_stmt};"
    )

SELECT_MATCH_QUERY= (
    "SELECT w.word_id, w.wordform, w.pos, w.feats, "
    # "w.update_info, "
    # "w.source, w.decomp_ort, w.decomp_pos, w.garbage, "
    # "w.domain, w.abbr, w.set_name, w.style_status, w.inflector_role, "
    # "w.inflector_rule, w.morph_label, w.compounder_code, "
    "p.pron_id, p.nofabet, p.certainty "
    "FROM {word_table} w "
    "LEFT JOIN {dialect} p ON p.word_id = w.word_id "
    "WHERE REGEXP(?,nofabet) "
    "{where_word_in_stmt};"
)

#!/usr/bin/env python
# coding=utf-8

__all__ = [
    "dialects",
    "word_table",
    "database",
    "rules",
    "exemptions",
    "output_dir",
    "rule_schema",
    "exemption_schema",
    "dialect_schema",
]

from schema import Schema

from .exemptions import exemption1, exemption2
from .rules import test1, test2

# Name of the temp table containing all
# words and word metadata in the backend dict
word_table = "words_tmp"

# Path to the backend dict
database = "./data/input/backend-db02.db"

# Path to the output folder for the lexica
output_dir = "./data/output"

# List of dialects which update rules can target.
# Corresponds to names of pronunciation temp tables
# created in the backend db
dialects = [
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
# Validation schema for dialects:
# The dialect variable is not reused here,
# to allow configurability of the list
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

# List of dialect update rules. Note that
# multiple rules may affect the same
# pronunciations, and that the ordering
# of the rules may matter.
rules = [test1, test2]

# Validation schema for the rulesets
rule_schema = Schema(
    [
        {
            "areas": dialects,
            "name": str,
            "rules": [
                {
                    "pattern": str,
                    "repl": str,
                    "constraints": [
                        {"field": str, "pattern": str, "is_regex": bool}
                    ],
                }
            ],
        }
    ]
)

# List of words to be exempted from the rules
exemptions = [exemption1, exemption2]
# Validation schema for the rulesets
exemption_schema = Schema([{"ruleset": str, "words": list}])

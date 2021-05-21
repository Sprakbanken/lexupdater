#!/usr/bin/env python
# coding=utf-8

"""Configure input data to update the lexicon transcriptions."""

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


word_table = "words_tmp"
"""Name of the temp table containing all words and word metadata 
in the backend db
"""

database = "./data/input/backend-db02.db"
"""Path to the backend db"""

output_dir = "./data/output"
"""Path to the output folder for the lexica"""


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
"""List of dialects which update rules can target.

Corresponds to names of pronunciation temp tables created in the backend db.
"""


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
"""Validation schema for dialects

The dialect variable is not reused here, to allow configurability of the list
"""


rules = [test1, test2]
"""List of dialect update rules. 

Note that multiple rules may affect the same  pronunciations, 
and that the ordering of the rules may matter.
"""


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
"""Validation schema for the rulesets"""


exemptions = [exemption1, exemption2]
"""List of dictionaries with words to be exempted from the rules"""


exemption_schema = Schema([{"ruleset": str, "words": list}])
"""Validation schema for the rulesets"""

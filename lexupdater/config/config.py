#!/usr/bin/env python
# coding=utf-8

"""Configure input data to update the lexicon transcriptions."""

from .exemptions import exemption_list
from .rules import rule_list
from .constants import dialect_schema, rule_schema, exemption_schema


__all__ = [
    "word_table",
    "database",
    "dialects",
    "rules",
    "exemptions",
    "output_dir",
]
"""Variables that are available to be imported 
by other modules.
"""


word_table = "words_tmp"
"""Name of the temp table containing all words and word metadata 
in the backend db
"""


database = "./data/input/backend-db02.db"
"""Path to the backend db"""


output_dir = "./data/output"
"""Path to the output folder for the lexica"""


dialects = dialect_schema.validate([
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
"""List of dialects which update rules can target.

Corresponds to names of pronunciation temp tables created in the backend db.
"""


rules = rule_schema.validate(rule_list)
"""List of dialect update rules. 

Note that multiple rules may affect the same  pronunciations, 
and that the ordering of the rules may matter.
"""


exemptions = exemption_schema.validate(exemption_list)
"""List of dictionaries with words to be exempted from the rules"""

#!/usr/bin/env python
# coding=utf-8

from .exemptions import exemption_list
from .rules import rule_list
from .constants import dialect_schema, rule_schema, exemption_schema

# When config is imported in another module,
# these are the variables available for import
__all__ = [
    "word_table",
    "database",
    "dialects",
    "rules",
    "exemptions",
    "output_dir",
    "rule_schema",
    "exemption_schema",
    "dialect_schema",
]


# Name of the temp table to be created
# containing words and word metadata in the backend db
word_table = "words_tmp"

# Path to the backend db
database = "./data/input/backend-db02.db"

# Path to the output folder for the lexica
output_dir = "./data/output"

# List of dialects which update rules can target.
# Corresponds to names of pronunciation temp tables
# created in the backend db.
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

# List of dialect update rules. Note that
# multiple rules may affect the same
# pronunciations, and that the ordering
# of the rules may matter.
rules = rule_schema.validate(rule_list)

# List of words to be exempted from the rules
exemptions = exemption_schema.validate(exemption_list)

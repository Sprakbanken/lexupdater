#!/usr/bin/env python
# coding=utf-8

"""Configure input data to update the lexicon transcriptions."""

from pathlib import Path

from .exemptions import EXEMPTIONS
from .rules import RULES


__all__ = [
    "WORD_TABLE",
    "DATABASE",
    "DIALECTS",
    "RULES",
    "EXEMPTIONS",
    "OUTPUT_DIR",
]
"""Variables that are available to be imported
by other modules.
"""


WORD_TABLE = "words_tmp"
"""Name of the temp table containing all words and word metadata
in the backend db
"""

DATA_DIR = Path("data")

INPUT_DIR = DATA_DIR / "input"

DATABASE = INPUT_DIR / "backend-db02.db"
"""Path to the backend db"""


OUTPUT_DIR = DATA_DIR / "output"
"""Path to the output folder for the lexica"""


DIALECTS = [
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

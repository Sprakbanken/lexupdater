"""Configure input data to update the lexicon transcriptions."""

DATABASE = "backend-db03.db"
"""Path to the backend db"""

OUTPUT_DIR = "lexica"
"""Path to the output folder for the lexica"""

RULES_FILE = "rules.py"
"""Path to file with dialect update rules.

Note that multiple rules may affect the same  pronunciations,
and that the ordering of the rules may matter.
"""

EXEMPTIONS_FILE = "exemptions.py"
"""Path to file with exemption dicts"""

NEWWORD_FILES = [
        "nyord.csv",
        "nyord02.csv"
    ]
"""A list of file paths to csv files containing newword tables"""

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

VALID_PHONEMES = "phoneme_inventory.txt"
"""List of valid phonemes for the transcriptions of the database."""
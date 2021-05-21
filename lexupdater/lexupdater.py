#!/usr/bin/env python
# coding=utf-8

"""Transcription updates for a pronunciation lexicon in sqlite3 db format."""

import datetime

from .config import (
    WORD_TABLE,
    DATABASE,
    RULES,
    EXEMPTIONS,
    OUTPUT_DIR
)
from .db_handler import DatabaseUpdater


def get_base(connection):
    """
    Select the state of the lexicon before the updates.

    Parameters
    ----------
    connection: sqlite3.connect
        A connection to the open sqlite database

    Returns
    -------
    result: list
        The full contents of the base lexicon
    """
    stmt = """SELECT w.word_id, w.wordform, w.pos, w.feats, w.source,
            w.decomp_ort, w.decomp_pos, w.garbage, w.domain, w.abbr,
            w.set_name, w.style_status, w.inflector_role, w.inflector_rule,
            w.morph_label, w.compounder_code, w.update_info, p.pron_id,
            p.nofabet, p.certainty FROM words w LEFT JOIN base p ON
            p.word_id = w.word_id;"""
    cursor = connection.cursor()
    result = cursor.execute(stmt).fetchall()
    return result


def main(print_dialects, print_base):
    """Apply the replacement rules from the config on the base lexicon.

    The variable base contains the original state of the lexicon.
    exp contains the modified lexicon based on the rules and
    exemptions specified in the config file. Note that all modifications
    in the backend db target temp tables, so the db isn"t modified.

    The modifications to the lexicon are written to new, dialect-specific
    files.

    Parameters
    ----------
    print_dialects: list
        List of dialects to write updated lexicon .txt-files for
    print_base: bool
        If True, write the base lexicon as a .txt-file
    """
    # For calculating execution time. Remove in stable version
    begin_time = datetime.datetime.now()

    update_obj = DatabaseUpdater(
        DATABASE, RULES, print_dialects, WORD_TABLE, exemptions=EXEMPTIONS
    )
    connection = update_obj.get_connection()
    update_obj.update()
    exp = update_obj.get_results()
    update_obj.close_connection()

    # For calculating execution time. Remove in stable version
    update_end_time = datetime.datetime.now()
    updatetime = update_end_time - begin_time
    print(f"Database updated. Time: {updatetime}")

    # Write a base and exp lexicon file for each dialect area d.
    for dialect in print_dialects:
        with open(f"{OUTPUT_DIR}/{dialect}.txt", "w") as expfile:
            for elm in exp[dialect]:
                expfile.write(f"{elm[1]}\t{elm[2]}\t{elm[3]}\t{elm[-2]}\n")

    if print_base:
        base = get_base(connection)
        with open(f"{OUTPUT_DIR}/base.txt", "w") as outfile:
            for item in base:
                outfile.write(f"{item[1]}\t{item[2]}\t{item[3]}\t{item[-2]}\n")

    # For calculating execution time. Remove in stable version
    filegen_end_time = datetime.datetime.now()
    filegentime = filegen_end_time - update_end_time
    print(f"Files generated. Time: {filegentime}")

#!/usr/bin/env python
# coding=utf-8

import argparse
import datetime

from .db_handler import DatabaseUpdater
from .config import dialects, word_table, database, rules, blacklists, output_dir


# For calculating execution time. Remove in stable version
begin_time = datetime.datetime.now()

# Argument parser
parser = argparse.ArgumentParser()

parser.add_argument(
    "--print_dialects",
    "-d",
    action="store",
    type=str,
    nargs="*",
    default=dialects,
    help=("Generate lexicon files for" " one or more specified dialects."),
)
parser.add_argument(
    "--print_base",
    "-b",
    action="store_true",
    help=(
        "Generate a base lexicon file,"
        "containing the state of the "
        "lexicon prior to updates."
    ),
)
args = parser.parse_args()


# Function to select the state of the lexicon before the updates


def get_base(connection):
    stmt = """SELECT w.word_id, w.wordform, w.pos, w.feats, w.source,
            w.decomp_ort, w.decomp_pos, w.garbage, w.domain, w.abbr,
            w.set_name, w.style_status, w.inflector_role, w.inflector_rule,
            w.morph_label, w.compounder_code, w.update_info, p.pron_id,
            p.nofabet, p.certainty FROM words w LEFT JOIN base p ON
            p.word_id = w.word_id;"""
    cursor = connection.cursor()
    result = cursor.execute(stmt).fetchall()
    return result


# The variable base contains the original state of the lexicon.
# exp contains the modified lexicon based on the rules and
# blacklists specified in the config file. Note that all modifications
# in the backend db target temp tables, so the db isn"t modified.

updateobj = DatabaseUpdater(
    database, rules, dialects, word_table, blacklists=blacklists
)
connection = updateobj.get_connection()
updateobj.update()
exp = updateobj.get_results()
updateobj.close_connection()

# For calculating execution time. Remove in stable version
update_end_time = datetime.datetime.now()
updatetime = update_end_time - begin_time
print(f"Database updated. Time: {updatetime}")

# Write a base and exp lexicon file for each dialect area d.

for d in args.print_dialects:
    with open(f"{output_dir}/{d}.txt", "w") as expfile:
        for elm in exp[d]:
            expfile.write(f"{elm[1]}\t{elm[2]}\t{elm[3]}\t{elm[-2]}\n")


if args.print_base:
    base = get_base(connection)
    with open(f"{output_dir}/base.txt", "w") as basefile:
        for el in base:
            basefile.write(f"{el[1]}\t{el[2]}\t{el[3]}\t{el[-2]}\n")

# For calculating execution time. Remove in stable version
filegen_end_time = datetime.datetime.now()
filegentime = filegen_end_time - update_end_time
print(f"Files generated. Time: {filegentime}")

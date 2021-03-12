#!/usr/bin/env python
# coding=utf-8

from bin import DatabaseUpdater
from config import dialects, word_table, database, rules, blacklists

# Function to select the state of the lexicon before the updates

def get_base(connection, dialects):
    stmt = """SELECT w.word_id, w.wordform, w.pos, w.feats, w.source, w.decomp_ort, w.decomp_pos, 
                w.garbage, w.domain, w.abbr, w.set_name, w.style_status, w.inflector_role, w.inflector_rule, 
                w.morph_label, w.compounder_code, w.update_info, p.pron_id, p.nofabet, p.certainty
                FROM words w LEFT JOIN base p ON p.word_id = w.word_id;"""
    cursor = connection.cursor()
    result = cursor.execute(stmt).fetchall()
    return {d:result for d in dialects}



# The variable base contains the original state of the lexicon. exp contains the modified lexicon
# based on the rules and blacklists specified in the config file. Note that all modifications
# in the backend db target temp tables, so the db isn't modified.

updateobj = DatabaseUpdater(database, rules, dialects, word_table, blacklists=blacklists)
connection = updateobj.get_connection()
base = get_base(connection, dialects)
updateobj.update()
exp = updateobj.get_results()
updateobj.close_connection()

# Write a base and exp lexicon file for each dialect area d.

for d in ['e_spoken']:
    with open(f'{d}_base.txt', 'w') as basefile, open(f'{d}_exp.txt', 'w') as expfile:
        for el in base[d]:
            basefile.write(f'{el[1]}\t{el[2]}\t{el[3]}\t{el[-2]}\n')
        for elm in exp[d]:
            expfile.write(f'{elm[1]}\t{elm[2]}\t{elm[3]}\t{elm[-2]}\n')


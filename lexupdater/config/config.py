#!/usr/bin/env python
# coding=utf-8

__all__ = ['dialects', 'word_table', 'database', 'rules', 'blacklists', 'output_dir']

from .rules import test1, test2
from .blacklists import blacklist1, blacklist2


# List of dialects which update rules can target. Corresponds to names of pronunciation temp tables 
# created in the backend db
dialects =  ['e_spoken', 'e_written', 'sw_spoken', 'sw_written', 'w_spoken', 'w_written', 
            't_spoken', 't_written', 'n_spoken', 'n_written']


# Name of the temp table containing all words and word metadata in the backend dict
word_table = "words_tmp"

# Path to the backend dict
database = './data/input/backend-db02.db'

# Path to the output folder for the lexica
output_dir = "./data/output"

# List of dialect update rules. Note that multiple rules may affect the same pronunciations, and that the ordering
# of the rules may matter.
rules = [
            test1, 
            test2
        ]

# List of blacklists
blacklists = [blacklist1, blacklist2]

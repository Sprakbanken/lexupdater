#!/usr/bin/env python
# coding=utf-8

import pandas as pd


"""Lists of new words

Lists of new words to be added to the lexicon are specified in
csv files, which are loaded into the dataframe "newwords".

These are the columns of "newwords":
    "token": the orthographic form
    "transcription": The primary phonetic transcription
    "alt_transcription_1-3": Alternative transcriptions. May be empty
    "pos": The POS tag
    "morphology": Morphological features. May be empty

The csv files may contain additional columns, but these will not be loaded
into "newwords"
"""

newword_csv_paths = [
    "nyord.csv",
    "nyord02.csv"
]
"""List of csv files with new words"""

column_names = [
    "token",
    "transcription",
    "alt_transcription_1",
    "alt_transcription_2",
    "alt_transcription_3",
    "pos",
    "morphology"
]
"""Names of the columns in the newword df"""

_df_list = []

for path in newword_csv_paths:
    df = pd.read_csv(path, header=0, index_col=None)[column_names]
    _df_list.append(df)

newwords = pd.concat(_df_list, axis=0, ignore_index=True)
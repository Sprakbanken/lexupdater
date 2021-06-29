"""Parse DataFrames with lexical additions.

Parse DataFrames with lexical additions
into lists of variables to fill slots in SQL query templates.
"""

from typing import Tuple
import pandas as pd

from .constants import UNIQUE_ID_PATTERN

def _make_pron_table(newwords, proncolumnname):
    pron_df = newwords[
        [proncolumnname, "unique_id"]
    ][~newwords[proncolumnname].isna()]
    pron_df["certainty"] = 1
    pron_df.columns = ["transcription", "unique_id", "certainty"]
    return pron_df

def _process_newword_table(newwords):
    newwords["unique_id"] = newwords.apply(
        lambda row: UNIQUE_ID_PATTERN.format(counter=row.name),
        axis=1
    )
    word_df = newwords[
        ["token", "pos", "morphology", "unique_id"]
    ]
    pron_df = pd.concat(
        [
            _make_pron_table(newwords, "transcription"),
            _make_pron_table(newwords, "alt_transcription_1"),
            _make_pron_table(newwords, "alt_transcription_2"),
            _make_pron_table(newwords, "alt_transcription_3")
        ],
        ignore_index=True
    )
    return (word_df, pron_df)

def parse_newwords(newwords: pd.DataFrame) -> Tuple: 
    """Convert a DataFrame with lexical additions to a pair
    of lists of values to SQL insert statements.

    Parameters
    ----------
    newword_df: 
        a DataFrame with lexical additions and
        corresponding transcriptions and grammatical
        information.

    Returns
    -------
    tuple[list, list]
        a list of word table values and
        a list of pron table values
    """
    word_df, pron_fd = _process_newword_table(newwords)
    word_values, pron_values = [
        (list(df.itertuples(index=False, name=None)))
        for df in [word_df, pron_fd]
    ]
    return (word_values, pron_values)







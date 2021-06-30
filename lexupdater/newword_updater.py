"""Parse DataFrames with lexical additions.

Parse DataFrames with lexical additions
into lists of variables to fill slots in SQL query templates.
"""

from typing import Tuple
import pandas as pd

from .constants import UNIQUE_ID_PATTERN, newword_schema

def _make_pron_table(newwords, pron_column_name):
    pron_df = newwords[
        [pron_column_name, "unique_id"]
    ][~newwords[pron_column_name].isna()]
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
    newwords_df = newword_schema.validate(newwords)
    word_df, pron_df = _process_newword_table(newwords_df)
    word_values, pron_values = [
        (list(df.itertuples(index=False, name=None)))
        for df in [word_df, pron_fd]
    ]
    return (word_values, pron_values)

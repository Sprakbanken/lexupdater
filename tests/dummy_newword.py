from lexupdater.utils import _load_newwords

_newword_csv_paths = [
        "nyord.csv",
        "nyord02.csv"
    ]

_column_names = [
        "token",
        "transcription",
        "alt_transcription_1",
        "alt_transcription_2",
        "alt_transcription_3",
        "pos",
        "morphology"
    ]

newwords = _load_newwords(_newword_csv_paths, _column_names)[:5]

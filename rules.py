"""Pronunciation replacement rulesets.

"areas" is the list of dialects which should be affected by the rule.
    Dialect names are specified in config.py.

"name" is the name of the ruleset.
    These should be unique, and are mapped to exemption words.

"rules" contains a list of replacement rules.
    Each rule consists of
    "pattern", which is a regex pattern for a certain transcription,
    "repl" which is a replacement referencing the pattern,
    and "constraints", a(n optionally empty) list of dicts constraining
    the replacement only to words with given metadata.
    In the constraints dicts,
        "field" gives the word metadata field (corresponding to fields in the
        NST lexicon),
        "pattern" is the pattern that should be matched in the field,
        either a regex or a literal,
        and "is_regex", which should be True if the pattern is a regex and
        False otherwise.

Note that multiple rules may affect the same  pronunciations,
and that the ordering of the rules may be of importance for the result.
"""


test1 = {
    "areas": ["e_spoken"],
    "name": "retrotest",
    "rules": [
        {"pattern": r"\b(R)([NTD])\b", "repl": r"\1 \2", "constraints": []},
        {"pattern": r"\b(R)(NX0)\b", "repl": r"\1 AX0 N", "constraints": []},
    ],
}


test2 = {
    "areas": ["n_written", "n_spoken", "sw_written", "sw_spoken"],
    "name": "masc",
    "rules": [
        {
            "pattern": r"\bAX0 R$",
            "repl": r"AA0 R",
            "constraints": [
                {"field": "pos", "pattern": r"NN", "is_regex": False},
                {"field": "feats", "pattern": r"MAS", "is_regex": True},
            ],
        },
        {
            "pattern": r"\bNX0 AX0$",
            "repl": r"AA0 N AX0",
            "constraints": [
                {"field": "pos", "pattern": r"NN", "is_regex": False},
                {"field": "feats", "pattern": r"MAS", "is_regex": True},
            ],
        },
    ],
}

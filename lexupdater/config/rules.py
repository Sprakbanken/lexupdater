#!/usr/bin/env python
# coding=utf-8

# Pronunciation replacement rulesets. "area" is the dialect which should be
# affected by the rule. For now it only supports a single dialect, but in the
# final version, it should take a list. Dialect names are specified in the
# config file. "name" is the name of the ruleset. These should be unique, as
# blacklists make reference to them. "rules" contains a list of
# replacement rules. Each rule consists of a "pattern", which is
# a regex pattern for a certain transcription, "repl" which is a
# replacement referencing the pattern, and a possibly empty list
# of constraints, constraining the replacement only to words with
# given metadata. In the costraint dicts, "field" gives the word
# metadata field (corresponing to fields in the NST lexicon), "pattern"
# is the pattern that should be matched in the field, either
# a regex or a literal, and "is_regex", which should be True if the pattern
# is a regex and False otherwise.


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

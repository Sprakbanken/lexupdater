"""Dummy values to test how lexupdater handles rules."""

test1 = {
    "areas": ["e_spoken"],
    "name": "retrotest",
    "rules": [
        {
            "pattern": r"\b(R)([NTD])\b",
            "replacement": r"\1 \2",
            "constraints": []},
        {
            "pattern": r"\b(R)(NX0)\b",
            "replacement": r"\1 AX0 N",
            "constraints": []},
    ],
}


test2 = {
    "areas": ["n_written", "n_spoken", "sw_written", "sw_spoken"],
    "name": "masc",
    "rules": [
        {
            "pattern": r"\bAX0 R$",
            "replacement": r"AA0 R",
            "constraints": [
                {"field": "pos", "pattern": r"NN", "is_regex": False},
                {"field": "feats", "pattern": r"MAS", "is_regex": True},
            ],
        },
        {
            "pattern": r"\bNX0 AX0$",
            "replacement": r"AA0 N AX0",
            "constraints": [
                {"field": "pos", "pattern": r"NN", "is_regex": False},
                {"field": "feats", "pattern": r"MAS", "is_regex": True},
            ],
        },
    ],
}

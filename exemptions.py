#!/usr/bin/env python
# coding=utf-8

"""List of dicts with words to be exempted from the specified rulesets."""

exemption1 = {"ruleset": "retrotest", "words": ["garn", "klarne"]}

exemption2 = {
    "ruleset": "masc",
    "words": ["søknader", "søknadene", "dugnader", "dugnadene"],
}

exemptions_list = [exemption1, exemption2]

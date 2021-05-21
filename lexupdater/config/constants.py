from schema import Schema, Optional


dialect_schema = Schema([
    "e_spoken",
    "e_written",
    "sw_spoken",
    "sw_written",
    "w_spoken",
    "w_written",
    "t_spoken",
    "t_written",
    "n_spoken",
    "n_written",
])
"""Validation schema for dialects

The dialect variable is not reused here, 
to allow configurability of the list.
"""


rule_schema = Schema(
    [
        {
            "areas": dialect_schema.schema,
            "name": str,
            "rules": [
                {
                    "pattern": str,
                    "repl": str,
                    "constraints": [
                        Optional({
                            "field": str,
                            "pattern": str,
                            "is_regex": bool
                        })
                    ],
                }
            ],
        }
    ]
)
"""Validation schema for the rulesets"""


exemption_schema = Schema([{"ruleset": str, "words": list}])
"""Validation schema for the exemptions"""

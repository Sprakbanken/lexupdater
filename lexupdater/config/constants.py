from schema import Schema, And, Or, Optional


# Validation schema for dialects:
# Do not change this variable!
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

# Validation schema for the rulesets
ruleset_schema = Schema(
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
)

# Validation schema for the exemptions
exemption_schema = Schema([{"ruleset": str, "words": list}])

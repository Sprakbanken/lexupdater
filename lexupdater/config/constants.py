from schema import Schema, Optional

from .config import DIALECTS

dialect_schema = Schema(DIALECTS)
"""Validation schema for dialects"""

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
"""Validation schema for the rulesets"""


exemption_schema = Schema([{"ruleset": str, "words": list}])
"""Validation schema for the exemptions"""

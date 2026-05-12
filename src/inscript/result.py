"""Structured result objects returned by every interpreter call.

Sources:
- v1c §50 (five outcome taxonomy)
- v1d §64 (interpreter never calls input/print; CLI wraps display & prompts)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ResultStatus(Enum):
    SUCCESS = "success"
    AMBER_PRECEDENCE = "amber_precedence"   # v1a §30: mixed and/or in where
    AMBER_AMBIGUITY = "amber_ambiguity"     # inception §17: reorderer ambiguity
    ERROR_PARSE = "error_parse"             # v1c §50 outcome 4
    ERROR_SEMANTIC = "error_semantic"       # v1c §50 outcome 5


@dataclass
class InscriptResult:
    status: ResultStatus
    canonical: str | None = None
    output: list[str] | None = None
    message: str | None = None
    executed: bool = False
    # `pending_ast` carries the parsed-but-not-executed AST through an amber
    # outcome so the CLI wrapper can resume after user confirmation
    # (v1d §64: two-step flow keeps the core interpreter stateless).
    pending_ast: Any = field(default=None, repr=False)

"""Vocabulary tables and token types for Inscript v1 / v2a / v2d.

Sources:
- inception §11 (vocabulary table), §17 (verb signatures), §22 (lexer rules)
- v1a §29 (reserved words, 28-word total — superseded)
- v1c §47 (article `an`, reserved word count corrected to 29)
- v2a §67 (`keep` verb — non-destructive filter)
- v2a §68 (`of` connective — single-record field access)
- v2a §73 (updated vocabulary: 8 verbs, 10 connectives, 31 reserved words)
- v2d §99 (`choose` promoted from deferred to active verb)
- v2d §99 (`if` and `otherwise` connectives added)
- v2d §104 (updated vocabulary: 9 verbs, 12 connectives, 33 reserved words)
"""

from dataclasses import dataclass
from enum import Enum


class TokenType(Enum):
    VERB = "VERB"
    CONNECTIVE = "CONNECTIVE"
    OPERATOR = "OPERATOR"
    ARTICLE = "ARTICLE"
    DELIMITER = "DELIMITER"
    NUMBER = "NUMBER"
    UNKNOWN = "UNKNOWN"
    # v2c §86: a quoted string emitted by the lexer as a single token,
    # bypasses vocabulary lookup (§89) and is valid only in value
    # positions per §87.
    QUOTED_STRING = "QUOTED_STRING"


@dataclass
class Token:
    type: TokenType
    value: str
    position: int


# v1 / v2a / v2d verbs. v2a §67 added `keep`. v2d §99 promoted `choose`
# from the v2-deferred table to an active verb.
VERBS: frozenset[str] = frozenset({
    "remember", "show", "filter", "keep",
    "count", "gather", "combine", "each",
    "choose",
})

# v1 / v2a / v2d connectives. v2a §68 added `of`. v2d §99 added `if`
# (introduces a `choose` condition) and `otherwise` (introduces a
# `choose` alternative branch).
CONNECTIVES: frozenset[str] = frozenset({
    "where", "and", "or", "from", "with", "called", "to", "how", "as", "of",
    "if", "otherwise",
})

# v1 single-word operators (inception §11). `equal to` is a multi-word
# operator combined by the lexer (inception §22) into a single OPERATOR
# token whose value is "equal_to" — see lexer.
OPERATORS: frozenset[str] = frozenset({
    "is", "above", "below", "not",
})

# v1 articles. `an` added in v1c §47 (previously the table listed `the`, `a`).
ARTICLES: frozenset[str] = frozenset({
    "the", "a", "an",
})

# Lone delimiter (inception §22)
DELIMITERS: frozenset[str] = frozenset({":"})

# v2 deferred words — designed but not executable in v1. Reserved so
# user programs that use them as names will not silently break when v2
# ships (v1a §29). v2d §99 promoted `choose` to an active verb, so it
# is no longer in this set. `when` and `unless` remain deferred for
# event-driven execution; `transform` and `compare` continue to be
# deferred per v2d §103.
V2_RESERVED: frozenset[str] = frozenset({
    "transform", "compare", "when", "unless",
})

# `equal` is the multi-word lookahead trigger for `equal to`. Reserved
# independently — allowing it as a name would make the lexer's behavior
# dependent on what word follows (v1a §29, v1c §47).
MULTI_WORD_RESERVED: frozenset[str] = frozenset({"equal"})

# All 33 reserved words (v2d §104: was 31 in v2a §73; +1 for `choose`
# promoted from deferred, +2 for `if` and `otherwise`. `choose` shifted
# from V2_RESERVED into VERBS, so the deferred set shrank by 1).
ALL_RESERVED: frozenset[str] = (
    VERBS | CONNECTIVES | OPERATORS | ARTICLES | V2_RESERVED | MULTI_WORD_RESERVED
)


def reserved_category(word: str) -> str | None:
    """Return the user-facing category name for a reserved word.

    Used by the parser to produce the v1a §29 reserved-word error message:
    "The word '[word]' is reserved in Inscript — it's used as a [category]."
    Returns None if the word is not reserved.
    """
    if word in VERBS:
        return "verb"
    if word in CONNECTIVES:
        return "connective"
    if word in OPERATORS or word in MULTI_WORD_RESERVED:
        return "operator"
    if word in ARTICLES:
        return "article"
    if word in V2_RESERVED:
        return "reserved word"
    return None


# Verb signatures (inception §17, refined by v1b/v1c/v1d). Each verb maps
# to the ordered list of slot names the parser must fill. Detailed parsing
# rules live in parser.py — this dict is the index of slots used by the
# reorderer and by tests as a structural reference.
VERB_SIGNATURES: dict[str, list[str]] = {
    "remember": ["name", "value"],
    "show":     ["target"],
    "filter":   ["target", "condition"],
    # v2a §67: `keep` shares filter's slots; only the interpreter differs
    # (filter mutates in place; keep returns a new list, source unchanged).
    "keep":     ["target", "condition"],
    "count":    ["target"],
    "gather":   ["name", "from", "to"],
    "combine":  ["target"],
    "each":     ["collection", "action"],
    # v2d §99: condition (after `if`), consequence (after `:`), and
    # alternative (after `otherwise`, optional).
    "choose":   ["condition", "consequence", "alternative"],
}

"""Vocabulary tables and token types for Inscript v1.

Sources:
- inception §11 (vocabulary table), §17 (verb signatures), §22 (lexer rules)
- v1a §29 (reserved words, 28-word total — superseded)
- v1c §47 (article `an`, reserved word count corrected to 29)
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


@dataclass
class Token:
    type: TokenType
    value: str
    position: int


# v1 verbs (inception §11)
VERBS: frozenset[str] = frozenset({
    "remember", "show", "filter", "count", "gather", "combine", "each",
})

# v1 connectives (inception §11)
CONNECTIVES: frozenset[str] = frozenset({
    "where", "and", "or", "from", "with", "called", "to", "how", "as",
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

# v2 deferred words — designed but not executable in v1. Reserved now so
# user programs that use them as names will not silently break when v2 ships
# (v1a §29).
V2_RESERVED: frozenset[str] = frozenset({
    "transform", "choose", "compare", "when", "unless",
})

# `equal` is the multi-word lookahead trigger for `equal to`. Reserved
# independently — allowing it as a name would make the lexer's behavior
# dependent on what word follows (v1a §29, v1c §47).
MULTI_WORD_RESERVED: frozenset[str] = frozenset({"equal"})

# All 29 reserved words (v1c §47 corrected total).
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
    "count":    ["target"],
    "gather":   ["name", "from", "to"],
    "combine":  ["target"],
    "each":     ["collection", "action"],
}

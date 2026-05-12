"""Lexer for Inscript v1.

Sources:
- inception §22 (lexer specification)
- v1c §47 (article `an` recognized)
- v1c §48 (blank lines produce zero tokens)
- v1d §57 (lexer lowercases — symbol table names are lowercase as a consequence)

Algorithm per BUILD_PLAN Phase 2:
1. Empty / whitespace-only line → return [] (v1c §48).
2. Tokenize the original-cased line into raw words, splitting on whitespace
   and isolating `:` as its own token (§22 line 434).
3. Strip decorative punctuation `, . ? !` from each word's edges (§22 line 430).
   Internal `.` is preserved so `3.14` survives.
4. Lowercase each word (§22 line 424).
5. Combine `equal` + `to` into a single OPERATOR token `equal_to` via
   one-word lookahead (§22 line 426).
6. Classify each word against the vocabulary tables, falling back to NUMBER
   (digits + optional single decimal point, §22 line 428) and finally UNKNOWN.

`equal` not followed by `to` falls through to UNKNOWN; the parser catches it
as a reserved-word violation when it appears in a name position (v1a §29).
"""

from __future__ import annotations

import re

from .vocabulary import (
    ARTICLES,
    CONNECTIVES,
    OPERATORS,
    Token,
    TokenType,
    VERBS,
)

_DECORATIVE = ",.?!"
_NUMBER_RE = re.compile(r"^\d+(?:\.\d+)?$")


def tokenize(line: str) -> list[Token]:
    """Lex a single source line into tokens.

    Returns an empty list for blank or whitespace-only lines (v1c §48).
    Positions are character offsets into the original input line.
    """
    if not line.strip():
        return []

    raw: list[tuple[str, int]] = _split_raw(line)
    cleaned: list[tuple[str, int]] = _strip_and_lower(raw)
    return _classify(cleaned)


def _split_raw(line: str) -> list[tuple[str, int]]:
    """Split the line on whitespace, with `:` isolated as its own token."""
    out: list[tuple[str, int]] = []
    i = 0
    n = len(line)
    while i < n:
        c = line[i]
        if c.isspace():
            i += 1
            continue
        if c == ":":
            out.append((":", i))
            i += 1
            continue
        start = i
        while i < n and not line[i].isspace() and line[i] != ":":
            i += 1
        out.append((line[start:i], start))
    return out


def _strip_and_lower(raw: list[tuple[str, int]]) -> list[tuple[str, int]]:
    """Strip decorative punctuation from each word's edges and lowercase.

    Edges only — interior `.` survives so `3.14` remains intact.
    Empty residues (e.g. a stray `,`) are dropped.
    """
    out: list[tuple[str, int]] = []
    for word, pos in raw:
        left = 0
        while left < len(word) and word[left] in _DECORATIVE:
            left += 1
        right = len(word)
        while right > left and word[right - 1] in _DECORATIVE:
            right -= 1
        if left == right:
            continue
        out.append((word[left:right].lower(), pos + left))
    return out


def _classify(cleaned: list[tuple[str, int]]) -> list[Token]:
    tokens: list[Token] = []
    j = 0
    while j < len(cleaned):
        word, pos = cleaned[j]

        if word == ":":
            tokens.append(Token(TokenType.DELIMITER, ":", pos))
            j += 1
            continue

        # Multi-word lookahead: `equal` + `to` -> `equal_to` operator (§22).
        # The token's position is the position of `equal`.
        if (
            word == "equal"
            and j + 1 < len(cleaned)
            and cleaned[j + 1][0] == "to"
        ):
            tokens.append(Token(TokenType.OPERATOR, "equal_to", pos))
            j += 2
            continue

        if word in VERBS:
            tokens.append(Token(TokenType.VERB, word, pos))
        elif word in CONNECTIVES:
            tokens.append(Token(TokenType.CONNECTIVE, word, pos))
        elif word in OPERATORS:
            tokens.append(Token(TokenType.OPERATOR, word, pos))
        elif word in ARTICLES:
            tokens.append(Token(TokenType.ARTICLE, word, pos))
        elif _NUMBER_RE.match(word):
            tokens.append(Token(TokenType.NUMBER, word, pos))
        else:
            tokens.append(Token(TokenType.UNKNOWN, word, pos))
        j += 1
    return tokens

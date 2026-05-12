"""Phase 5 gate tests: semantic analyzer (inception §23, v1b §38, v1c §49,
v1d §59/§60/§62/§63).
"""

import pytest

from inscript.analyzer import SymbolEntry, analyze
from inscript.lexer import tokenize
from inscript.parser import (
    CompositionCallNode,
    EachNode,
    NameRef,
    ShowNode,
    parse,
)
from inscript.reorderer import reorder
from inscript.result import InscriptResult, ResultStatus


def _parse(line: str, comps: set[str] | None = None):
    tokens = tokenize(line)
    reordered = reorder(tokens)
    assert not isinstance(reordered, InscriptResult), reordered
    ast = parse(reordered, composition_names=comps)
    assert not isinstance(ast, InscriptResult), ast
    return ast


def _analyze(line: str, symtab=None, comps: set[str] | None = None):
    return analyze(_parse(line, comps=comps), symtab or {})


# ---------------------------------------------------------------------------
# Convenience builders for symbol-table entries
# ---------------------------------------------------------------------------

def number(name, value):
    return SymbolEntry(name=name, value=value, type="number")


def string(name, value):
    return SymbolEntry(name=name, value=value, type="string")


def list_of_numbers(name, items):
    return SymbolEntry(name=name, value=list(items), type="list_of_numbers")


def list_of_strings(name, items):
    return SymbolEntry(name=name, value=list(items), type="list_of_strings")


def record(name, fields):
    schema = {}
    for k, v in fields.items():
        if isinstance(v, bool):
            schema[k] = "number"
        elif isinstance(v, (int, float)):
            schema[k] = "number"
        elif isinstance(v, str):
            schema[k] = "string"
        else:
            schema[k] = "unknown"
    return SymbolEntry(name=name, value=dict(fields), type="record", schema=schema)


def list_of_records(name, records_):
    return SymbolEntry(name=name, value=list(records_), type="list_of_records")


def composition(name, body_ast):
    return SymbolEntry(name=name, value=body_ast, type="composition")


# ---------------------------------------------------------------------------
# Happy paths
# ---------------------------------------------------------------------------

def test_show_known_name():
    symtab = {"age": number("age", 30)}
    result = _analyze("show age", symtab)
    assert not isinstance(result, InscriptResult)


def test_count_a_list():
    symtab = {"colors": list_of_strings("colors", ["red", "blue", "green"])}
    result = _analyze("count the colors", symtab)
    assert not isinstance(result, InscriptResult)


def test_filter_on_record_list_with_known_field():
    symtab = {
        "order1": record("order1", {"total": 75, "status": "active"}),
        "order2": record("order2", {"total": 30, "status": "active"}),
        "orders": list_of_records("orders", [
            {"total": 75, "status": "active"},
            {"total": 30, "status": "active"},
        ]),
    }
    result = _analyze("filter the orders where total is above 50", symtab)
    assert not isinstance(result, InscriptResult)


def test_filter_each_pronoun_on_flat_list():
    symtab = {"numbers": list_of_numbers("numbers", [1, 2, 3, 4, 5])}
    result = _analyze("filter the numbers where each is above 3", symtab)
    assert not isinstance(result, InscriptResult)


def test_each_iteration_over_records():
    symtab = {"orders": list_of_records("orders", [
        {"total": 75, "status": "active"},
        {"total": 30, "status": "active"},
    ])}
    result = _analyze("each the orders show total", symtab)
    assert not isinstance(result, InscriptResult)


def test_gather_valid_range():
    result = _analyze("gather the numbers from 1 to 10")
    assert not isinstance(result, InscriptResult)


def test_combine_list_of_numbers():
    symtab = {"numbers": list_of_numbers("numbers", [1, 2, 3])}
    result = _analyze("combine the numbers", symtab)
    assert not isinstance(result, InscriptResult)


def test_remember_value_with_literal():
    result = _analyze("remember a number called age with 30")
    assert not isinstance(result, InscriptResult)


def test_remember_value_with_existing_name_reference():
    symtab = {"the-data": list_of_numbers("the-data", [1, 2, 3])}
    result = _analyze("remember a copy called backup from the-data", symtab)
    assert not isinstance(result, InscriptResult)


def test_remember_list_homogeneous_strings():
    result = _analyze("remember a list called colors with red and blue and green")
    assert not isinstance(result, InscriptResult)


def test_remember_record():
    result = _analyze("remember an order called order1 with total as 75 and status as active")
    assert not isinstance(result, InscriptResult)


# ---------------------------------------------------------------------------
# Sentence 35 — name not found
# ---------------------------------------------------------------------------

def test_show_unknown_name_is_semantic_error():
    result = _analyze("show missingname")
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "missingname" in result.message
    assert "remember" in result.message


# ---------------------------------------------------------------------------
# Sentence 36 — filter on scalar
# ---------------------------------------------------------------------------

def test_filter_on_scalar_is_type_error():
    symtab = {"age": number("age", 30)}
    result = _analyze("filter age where each is above 5", symtab)
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "filter a list" in result.message
    assert "'age' is a number" in result.message


# ---------------------------------------------------------------------------
# Sentence 37 — combine on strings
# ---------------------------------------------------------------------------

def test_combine_strings_is_type_error():
    symtab = {"colors": list_of_strings("colors", ["red", "blue", "green"])}
    result = _analyze("combine colors", symtab)
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "only combine numbers" in result.message
    assert "'colors' contains text" in result.message


def test_combine_records_is_type_error():
    symtab = {"orders": list_of_records("orders", [{"total": 75}])}
    result = _analyze("combine orders", symtab)
    assert isinstance(result, InscriptResult)
    assert "'orders' contains records" in result.message


# ---------------------------------------------------------------------------
# Sentence 38 — field missing on records
# ---------------------------------------------------------------------------

def test_filter_field_missing_on_singleton_list_of_records():
    symtab = {
        "orders": list_of_records("orders", [
            {"total": 75, "status": "active"},
        ]),
    }
    result = _analyze("filter the orders where missingfield is above 50", symtab)
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "missingfield" in result.message
    assert "orders" in result.message


# ---------------------------------------------------------------------------
# Sentence 39 — each on scalar
# ---------------------------------------------------------------------------

def test_each_on_scalar_is_type_error():
    symtab = {"age": number("age", 30)}
    result = _analyze("each the age show", symtab)
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "iterate over a list" in result.message
    assert "'age' is a number" in result.message


# ---------------------------------------------------------------------------
# Sentence 40 — descriptor mismatch with value (succeeds)
# ---------------------------------------------------------------------------

def test_descriptor_number_with_string_value_succeeds():
    # v1b §36: descriptor is decorative; type inferred from value.
    result = _analyze("remember a number called label with hello")
    assert not isinstance(result, InscriptResult)


# ---------------------------------------------------------------------------
# Sentence 41 — mixed-type list
# ---------------------------------------------------------------------------

def test_mixed_type_list_is_semantic_error():
    result = _analyze("remember a list called mixed with 1 and blue")
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "can't mix" in result.message
    assert "'1' is a number" in result.message
    assert "'blue' is text" in result.message


# ---------------------------------------------------------------------------
# Sentence 42 — descending range
# ---------------------------------------------------------------------------

def test_descending_range_is_semantic_error():
    result = _analyze("gather the numbers from 10 to 1")
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "less than or equal to" in result.message
    assert "10" in result.message and "1" in result.message


def test_equal_endpoints_are_allowed():
    result = _analyze("gather the numbers from 5 to 5")
    assert not isinstance(result, InscriptResult)


# ---------------------------------------------------------------------------
# Sentence 43 — gather range cap
# ---------------------------------------------------------------------------

def test_gather_range_cap_is_semantic_error():
    result = _analyze("gather the numbers from 1 to 20000")
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "too large" in result.message
    assert "10,000" in result.message


def test_gather_just_under_cap_succeeds():
    result = _analyze("gather the numbers from 1 to 10000")
    assert not isinstance(result, InscriptResult)


def test_gather_just_over_cap_fails():
    result = _analyze("gather the numbers from 1 to 10001")
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC


# ---------------------------------------------------------------------------
# Sentence 46 — composition call body-level semantic error at call time
# ---------------------------------------------------------------------------

def test_composition_definition_validates_without_name_resolution():
    # The body references missingname; analyzer must NOT error at definition.
    result = _analyze("remember how to show-missing: show missingname")
    assert not isinstance(result, InscriptResult)


def test_composition_call_validates_body_at_call_time():
    body = _parse("show missingname")
    symtab = {"show-missing": composition("show-missing", body)}
    result = _analyze("show-missing", symtab, comps={"show-missing"})
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "missingname" in result.message


# ---------------------------------------------------------------------------
# Sentence 48 — schema mismatch in a list of records
# ---------------------------------------------------------------------------

def test_filter_on_mixed_schemas_field_not_in_all_records():
    symtab = {
        "mixed-records": list_of_records("mixed-records", [
            {"total": 75, "status": "active"},
            {"price": 30, "color": "red"},
        ]),
    }
    result = _analyze("filter the mixed-records where total is above 50", symtab)
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    # U2/U3: the offending record is named (the test fixture builds the
    # list with raw dicts rather than a `remember` chain, so the analyzer
    # falls back to a positional identifier — "Item 2" here).
    assert "doesn't have a field called 'total'" in result.message
    assert "Other items do have it" in result.message
    assert "mixed-records" in result.message


# ---------------------------------------------------------------------------
# Type checking for above/below in conditions (v1c §23 line 460)
# ---------------------------------------------------------------------------

def test_above_with_text_value_is_type_error():
    symtab = {"numbers": list_of_numbers("numbers", [1, 2, 3])}
    result = _analyze("filter the numbers where each is above hello", symtab)
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "above" in result.message
    assert "hello" in result.message


def test_above_with_text_field_is_type_error():
    symtab = {"orders": list_of_records("orders", [
        {"status": "active"},
        {"status": "pending"},
    ])}
    result = _analyze("filter the orders where status is above 5", symtab)
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "above" in result.message
    assert "status" in result.message


# ---------------------------------------------------------------------------
# Field-name access on a flat list rejects (must use `each`)
# ---------------------------------------------------------------------------

def test_field_name_on_flat_list_is_error():
    symtab = {"numbers": list_of_numbers("numbers", [1, 2, 3])}
    result = _analyze("filter the numbers where missingfield is above 5", symtab)
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_SEMANTIC
    assert "each" in result.message

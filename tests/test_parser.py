"""Phase 4 gate tests: parser (inception §17/§21/§22, v1a §29/§30/§33,
v1b §36/§37/§41/§43/§44, v1c §46/§51, v1d §65).
"""

import pytest

from inscript.lexer import tokenize
from inscript.parser import (
    BareWord,
    ChooseBranch,
    ChooseNode,
    CombineNode,
    CompositionCallNode,
    CompoundConditionNode,
    ConditionNode,
    CountNode,
    EachNode,
    EachPronoun,
    FieldAccessNode,
    FilterNode,
    GatherNode,
    NameRef,
    NumberLiteral,
    QuotedString,
    RememberCompositionNode,
    RememberListNode,
    RememberRecordNode,
    RememberValueNode,
    SequenceNode,
    ShowNode,
    parse,
)
from inscript.result import InscriptResult, ResultStatus


def parse_line(line: str, comps: set[str] | None = None):
    return parse(tokenize(line), composition_names=comps)


# ---------- remember: flat values ----------

def test_remember_number():
    ast = parse_line("remember a number called age with 30")
    assert ast == RememberValueNode(name="age", value=NumberLiteral(30))


def test_remember_decimal():
    ast = parse_line("remember a number called pi with 3.14")
    assert ast == RememberValueNode(name="pi", value=NumberLiteral(3.14))


def test_remember_string():
    ast = parse_line("remember a number called label with hello")
    # v1b §36: descriptor `number` is decorative; value is inferred from token.
    assert ast == RememberValueNode(name="label", value=BareWord("hello"))


def test_remember_descriptor_ignored():
    a = parse_line("remember a thing called x with 5")
    b = parse_line("remember a value called x with 5")
    c = parse_line("remember a called x with 5")  # no descriptor
    assert a == b == c == RememberValueNode(name="x", value=NumberLiteral(5))


def test_remember_an_article():
    # v1c §47: `an` recognized as article.
    ast = parse_line("remember an item called widget with 25")
    assert ast == RememberValueNode(name="widget", value=NumberLiteral(25))


# ---------- remember: lists ----------

def test_remember_list_strings():
    ast = parse_line("remember a list called colors with red and blue and green")
    assert ast == RememberListNode(
        name="colors",
        items=[BareWord("red"), BareWord("blue"), BareWord("green")],
    )


def test_remember_list_numbers():
    ast = parse_line("remember a list called nums with 1 and 2 and 3 and 4 and 5")
    assert ast == RememberListNode(
        name="nums",
        items=[NumberLiteral(i) for i in (1, 2, 3, 4, 5)],
    )


def test_remember_list_records_by_name():
    ast = parse_line("remember a list called orders with order1 and order2 and order3")
    assert ast == RememberListNode(
        name="orders",
        items=[BareWord("order1"), BareWord("order2"), BareWord("order3")],
    )


def test_remember_singleton_list_with_list_descriptor():
    # v1d §65 sentence 38: descriptor `list` forces list construction for
    # singleton `with X` so that downstream filter sees a list, not a record.
    ast = parse_line("remember a list called orders with order1")
    assert ast == RememberListNode(name="orders", items=[BareWord("order1")])


def test_remember_singleton_without_list_descriptor_is_flat_value():
    ast = parse_line("remember a value called x with order1")
    assert ast == RememberValueNode(name="x", value=BareWord("order1"))


# ---------- remember: records ----------

def test_remember_record_single_field():
    ast = parse_line("remember an order called order1 with total as 75")
    assert ast == RememberRecordNode(
        name="order1",
        fields=[("total", NumberLiteral(75))],
    )


def test_remember_record_multi_field():
    ast = parse_line("remember an order called order1 with total as 75 and status as active")
    assert ast == RememberRecordNode(
        name="order1",
        fields=[("total", NumberLiteral(75)), ("status", BareWord("active"))],
    )


def test_remember_record_missing_value_after_field():
    # v1d §65 sentence 45: malformed record.
    result = parse_line(
        "remember an order called order1 with total as 75 and status"
    )
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_PARSE
    assert "status" in result.message
    assert "as" in result.message


# ---------- remember: composition definition ----------

def test_remember_composition_simple():
    ast = parse_line(
        "remember how to find-big-orders: filter the orders where total is above 50"
    )
    assert isinstance(ast, RememberCompositionNode)
    assert ast.name == "find-big-orders"
    assert isinstance(ast.body, FilterNode)
    assert ast.body.target == NameRef("orders")
    assert ast.body.condition == ConditionNode(
        field=NameRef("total"), op="above", value=NumberLiteral(50),
    )


def test_remember_composition_with_sequenced_body():
    ast = parse_line(
        "remember how to count-active: filter the orders where status is active and count the orders"
    )
    assert isinstance(ast, RememberCompositionNode)
    assert ast.name == "count-active"
    assert isinstance(ast.body, SequenceNode)
    assert len(ast.body.operations) == 2
    assert isinstance(ast.body.operations[0], FilterNode)
    assert isinstance(ast.body.operations[1], CountNode)


# ---------- remember: from <verb-phrase> (v1b §43) ----------

def test_remember_from_verb_phrase_captures_result():
    ast = parse_line("remember the result called total from combine the numbers")
    assert isinstance(ast, RememberValueNode)
    assert ast.name == "total"
    assert isinstance(ast.value, CombineNode)
    assert ast.value.target == NameRef("numbers")


def test_remember_from_name_simple_reference():
    ast = parse_line("remember a copy called backup from the-data")
    assert ast == RememberValueNode(name="backup", value=NameRef("the-data"))


# ---------- show ----------

def test_show_name():
    assert parse_line("show age") == ShowNode(target=NameRef("age"))


def test_show_without_target():
    # v1c §49: `show` inside `each` may display the current iterator item.
    assert parse_line("show") == ShowNode(target=None)


# ---------- filter + conditions ----------

def test_filter_simple_above():
    ast = parse_line("filter the orders where total is above 50")
    assert ast == FilterNode(
        target=NameRef("orders"),
        condition=ConditionNode(NameRef("total"), "above", NumberLiteral(50)),
    )


def test_filter_equality_with_is():
    ast = parse_line("filter the orders where status is active")
    assert ast == FilterNode(
        target=NameRef("orders"),
        condition=ConditionNode(NameRef("status"), "is", BareWord("active")),
    )


def test_filter_each_pronoun_above():
    # v1b §37: `each` inside where -> pronoun.
    ast = parse_line("filter the numbers where each is above 5")
    assert ast.condition == ConditionNode(EachPronoun(), "above", NumberLiteral(5))


def test_filter_not_above():
    ast = parse_line("filter the scores where each is not above 7")
    assert ast.condition == ConditionNode(EachPronoun(), "not_above", NumberLiteral(7))


def test_filter_not_below():
    ast = parse_line("filter the scores where each is not below 3")
    assert ast.condition == ConditionNode(EachPronoun(), "not_below", NumberLiteral(3))


def test_filter_not_equal_to():
    ast = parse_line("filter the scores where each is not equal to 5")
    assert ast.condition == ConditionNode(EachPronoun(), "not_equal_to", NumberLiteral(5))


def test_filter_equal_to():
    ast = parse_line("filter the orders where total is equal to 75")
    assert ast.condition == ConditionNode(NameRef("total"), "equal_to", NumberLiteral(75))


def test_filter_compound_and():
    ast = parse_line("filter the orders where total is above 50 and status is active")
    assert isinstance(ast.condition, CompoundConditionNode)
    assert ast.condition.connector == "and"
    assert isinstance(ast.condition.left, ConditionNode)
    assert isinstance(ast.condition.right, ConditionNode)


def test_filter_compound_or():
    ast = parse_line("filter the orders where total is below 30 or status is pending")
    assert isinstance(ast.condition, CompoundConditionNode)
    assert ast.condition.connector == "or"


def test_filter_compound_precedence_and_binds_tighter_than_or():
    # `A and B or C` -> or(and(A,B), C)
    result = parse_line(
        "filter the orders where total is above 50 and status is active or status is pending"
    )
    # Mixed precedence -> AMBER, not a raw AST.
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.AMBER_PRECEDENCE
    ast = result.pending_ast
    assert isinstance(ast.condition, CompoundConditionNode)
    assert ast.condition.connector == "or"
    assert isinstance(ast.condition.left, CompoundConditionNode)
    assert ast.condition.left.connector == "and"


def test_amber_precedence_message_contains_parenthesized_form():
    result = parse_line(
        "filter the orders where total is above 50 and status is active or status is pending"
    )
    assert isinstance(result, InscriptResult)
    assert "(total is above 50 and status is active)" in result.message
    assert "status is pending" in result.message


def test_single_operator_chains_do_not_trigger_amber():
    # `A and B and C` -> no amber.
    ast = parse_line(
        "filter the orders where total is above 50 and total is below 100 and status is active"
    )
    assert isinstance(ast, FilterNode)


# ---------- count, combine, gather ----------

def test_count():
    assert parse_line("count the colors") == CountNode(target=NameRef("colors"))


def test_combine():
    assert parse_line("combine the numbers") == CombineNode(target=NameRef("numbers"))


def test_gather():
    assert parse_line("gather the numbers from 1 to 10") == GatherNode(
        name="numbers", from_val=1, to_val=10,
    )


# ---------- each (iteration verb) ----------

def test_each_show_field():
    ast = parse_line("each the orders show total")
    assert ast == EachNode(
        collection=NameRef("orders"),
        action=ShowNode(target=NameRef("total")),
    )


def test_each_show_current_item():
    ast = parse_line("each the age show")
    # The analyzer will reject this at semantic time; parser accepts.
    assert ast == EachNode(collection=NameRef("age"), action=ShowNode(target=None))


# ---------- operation sequencing (§21 rule 3) ----------

def test_sequenced_filter_and_show():
    ast = parse_line("filter nums where each is above 3 and show missingname")
    assert isinstance(ast, SequenceNode)
    assert len(ast.operations) == 2
    assert isinstance(ast.operations[0], FilterNode)
    assert isinstance(ast.operations[1], ShowNode)


def test_sequencing_inside_where_clause_is_compound_not_sequence():
    # `and` followed by a field reference inside `where` -> compound condition.
    ast = parse_line("filter the orders where total is above 50 and status is active")
    assert isinstance(ast, FilterNode)


# ---------- named composition call (v1b §41 fallback) ----------

def test_composition_call_falls_back_when_no_verb():
    ast = parse_line("find-big-orders", comps={"find-big-orders"})
    assert ast == CompositionCallNode(name="find-big-orders")


def test_no_verb_no_composition_is_parse_error():
    # Sentence 34.
    result = parse_line("orders total above 50")
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_PARSE
    assert "verb" in result.message.lower()


def test_no_verb_lists_available_verbs():
    result = parse_line("orders total above 50")
    msg = result.message
    for verb in ("remember", "show", "filter", "count", "gather", "combine", "each"):
        assert verb in msg


# ---------- reserved-word violations (v1a §29) ----------

def test_reserved_word_in_name_position_is_error():
    result = parse_line("remember a value called filter with 10")
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_PARSE
    assert "'filter'" in result.message
    assert "reserved" in result.message
    assert "verb" in result.message


def test_reserved_word_in_value_position_is_error():
    # v1c §46 / sentence 32.
    result = parse_line("remember a list called items with filter and blue")
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_PARSE
    assert "'filter'" in result.message


# ---------- gather with bad shape ----------

def test_gather_with_non_number_from_is_parse_error():
    result = parse_line("gather the numbers from hello to 10")
    assert isinstance(result, InscriptResult)
    assert result.status is ResultStatus.ERROR_PARSE


# ---------- coverage: every locked v1 sentence parses without crashing ----------

# Sentences that succeed in their own context. Some require a symbol-table
# context for composition fallback (sentence 46's call). We pass symbol
# names where required.

PARSEABLE = [
    ("remember a number called age with 30", None),
    ("remember a list called colors with red and blue and green", None),
    ("show age", None),
    ("show colors", None),
    ("count the colors", None),
    ("remember an order called order1 with total as 75 and status as active", None),
    ("remember an order called order2 with total as 30 and status as active", None),
    ("remember an order called order3 with total as 120 and status as pending", None),
    ("remember a list called orders with order1 and order2 and order3", None),
    ("each the orders show total", None),
    ("filter the orders where total is above 50", None),
    ("show orders", None),
    ("filter the orders where status is active", None),
    ("count the orders", None),
    ("each the orders show status", None),
    ("gather the numbers from 1 to 10", None),
    ("filter the numbers where each is above 5", None),
    ("count the numbers", None),
    ("combine the numbers", None),
    ("remember the result called total from combine the numbers", None),
    ("gather the scores from 1 to 10", None),
    ("filter the scores where each is not above 7", None),
    ("filter the scores where each is not below 3", None),
    ("filter the scores where each is not equal to 5", None),
    ("remember how to find-big-orders: filter the orders where total is above 50", None),
    ("remember how to count-active: filter the orders where status is active and count the orders", None),
    ("filter the orders where total is above 50 and status is active", None),
    ("filter the orders where total is below 30 or status is pending", None),
    ("filter the orders where total is equal to 75", None),
    ("remember an item called widget with 25", None),
    ("each the age show", None),
    ("remember a number called label with hello", None),
    ("show label", None),
    ("show-missing", {"show-missing"}),
    ("remember a list called nums with 1 and 2 and 3 and 4 and 5", None),
    ("filter nums where each is above 3 and show missingname", None),
    ("show nums", None),
    ("remember an item called item1 with price as 30 and color as red", None),
    ("remember a list called mixed-records with order1 and item1", None),
    ("filter the mixed-records where total is above 50", None),
]


@pytest.mark.parametrize("line,comps", PARSEABLE)
def test_every_parseable_sentence_yields_an_ast(line, comps):
    out = parse_line(line, comps=comps)
    # Some lines are AMBER; the rest are AST nodes.
    if isinstance(out, InscriptResult):
        assert out.status in (ResultStatus.AMBER_PRECEDENCE, ResultStatus.AMBER_AMBIGUITY)
    else:
        assert out is not None


# Sentences expected to be parse errors at this stage (semantic errors
# are checked in Phase 5; the parser still accepts them syntactically).
SYNTAX_ERROR_SENTENCES = [
    "remember a value called filter with 10",                # sentence 31
    "remember a list called items with filter and blue",     # sentence 32
    "orders total above 50",                                  # sentence 34
    "remember an order called order1 with total as 75 and status as active and status",  # 45
]


@pytest.mark.parametrize("line", SYNTAX_ERROR_SENTENCES)
def test_syntax_errors_produce_error_parse(line):
    out = parse_line(line)
    assert isinstance(out, InscriptResult)
    assert out.status is ResultStatus.ERROR_PARSE


# ---------- v2d §96: composition parameters ----------


def test_composition_definition_with_parameter():
    ast = parse_line(
        "remember how to find-big from data: keep the data where total is above 50"
    )
    assert isinstance(ast, RememberCompositionNode)
    assert ast.name == "find-big"
    assert ast.param == "data"


def test_composition_definition_without_parameter_has_none_param():
    ast = parse_line(
        "remember how to show-all: show orders"
    )
    assert isinstance(ast, RememberCompositionNode)
    assert ast.param is None


def test_composition_definition_param_reserved_word_rejected():
    out = parse_line(
        "remember how to find-big from filter: keep the orders where total is above 50"
    )
    assert isinstance(out, InscriptResult)
    assert out.status is ResultStatus.ERROR_PARSE
    assert "reserved" in out.message


def test_composition_call_with_parameter_argument():
    ast = parse_line("find-big from orders", comps={"find-big"})
    assert isinstance(ast, CompositionCallNode)
    assert ast.name == "find-big"
    assert ast.arg == "orders"


def test_composition_call_without_parameter_argument():
    ast = parse_line("find-big", comps={"find-big"})
    assert isinstance(ast, CompositionCallNode)
    assert ast.name == "find-big"
    assert ast.arg is None


def test_composition_call_arg_must_be_a_name_not_a_literal():
    out = parse_line("find-big from 5", comps={"find-big"})
    assert isinstance(out, InscriptResult)
    assert out.status is ResultStatus.ERROR_PARSE


def test_composition_call_arg_must_be_a_name_not_a_reserved_word():
    # v2d §96: names-only — reserved words are rejected at parse time.
    out = parse_line("find-big from filter", comps={"find-big"})
    assert isinstance(out, InscriptResult)
    assert out.status is ResultStatus.ERROR_PARSE
    assert "reserved" in out.message


def test_v2a_70_chaining_error_path_is_removed():
    """v2d §96 supersedes v2a §70: `<comp> from <name>` is now parameter
    passing, not a chaining error. The old wording must not appear."""
    out = parse_line("find-large from docs", comps={"find-large"})
    # Either a successful parse (parser-level) — Phase 5 catches the
    # mismatch semantically — or some other error, but NEVER the
    # superseded v2a §70 wording.
    if isinstance(out, InscriptResult):
        assert "Composition chaining isn't supported" not in (out.message or "")


def test_remember_from_composition_with_parameter_peek_ahead():
    """v2d §98 — `remember … from <comp> from <name>` is the two-from
    value-capture shape. Outer from = value capture; inner from = param."""
    ast = parse_line(
        "remember the results called big from find-big from orders",
        comps={"find-big"},
    )
    assert isinstance(ast, RememberValueNode)
    assert ast.name == "big"
    assert isinstance(ast.value, CompositionCallNode)
    assert ast.value.name == "find-big"
    assert ast.value.arg == "orders"


def test_remember_from_composition_without_parameter_still_works():
    ast = parse_line(
        "remember the n called n from count-active",
        comps={"count-active"},
    )
    assert isinstance(ast, RememberValueNode)
    assert isinstance(ast.value, CompositionCallNode)
    assert ast.value.name == "count-active"
    assert ast.value.arg is None


# ---------- v2d §99–§102: choose verb ----------


def test_choose_simple_if_otherwise():
    ast = parse_line(
        'choose if score is above 50: show "pass" otherwise show "fail"'
    )
    assert isinstance(ast, ChooseNode)
    assert len(ast.branches) == 2
    first, last = ast.branches
    assert isinstance(first.condition, ConditionNode)
    assert first.condition.field == NameRef("score")
    assert first.condition.op == "above"
    assert first.condition.value == NumberLiteral(50)
    assert isinstance(first.action, ShowNode)
    assert isinstance(first.action.target, QuotedString)
    assert first.action.target.content == "pass"
    assert last.condition is None
    assert isinstance(last.action, ShowNode)


def test_choose_without_otherwise():
    ast = parse_line('choose if score is above 50: show "pass"')
    assert isinstance(ast, ChooseNode)
    assert len(ast.branches) == 1
    assert ast.branches[0].condition is not None


def test_choose_multi_way_otherwise_if_chain():
    ast = parse_line(
        'choose if level is above 8: show "high" '
        'otherwise if level is above 3: show "medium" '
        'otherwise show "low"'
    )
    assert isinstance(ast, ChooseNode)
    assert len(ast.branches) == 3
    # All but the last branch carry a condition.
    assert ast.branches[0].condition is not None
    assert ast.branches[1].condition is not None
    assert ast.branches[2].condition is None


def test_choose_multi_statement_action_with_and():
    ast = parse_line(
        'choose if score is above 50: show "pass" and remember a value called result with pass '
        'otherwise show "fail" and remember a value called result with fail'
    )
    assert isinstance(ast, ChooseNode)
    assert len(ast.branches) == 2
    # Each branch's action is a SequenceNode of two operations.
    for br in ast.branches:
        assert isinstance(br.action, SequenceNode)
        assert len(br.action.operations) == 2


def test_choose_with_compound_condition():
    ast = parse_line(
        'choose if score is above 50 and color is red: show "match"'
    )
    assert isinstance(ast, ChooseNode)
    assert isinstance(ast.branches[0].condition, CompoundConditionNode)
    assert ast.branches[0].condition.connector == "and"


def test_choose_with_of_on_left_side_of_condition():
    """v2d §100 — value expressions on both sides; `of` works on the left."""
    ast = parse_line('choose if total of o1 is above 50: show "big"')
    assert isinstance(ast, ChooseNode)
    cond = ast.branches[0].condition
    assert isinstance(cond, ConditionNode)
    assert isinstance(cond.field, FieldAccessNode)
    assert cond.field.field == "total"
    assert cond.field.record_name == "o1"


def test_choose_with_of_on_both_sides_of_condition():
    ast = parse_line(
        'choose if total of o1 is above total of o2: show "o1 bigger"'
    )
    assert isinstance(ast, ChooseNode)
    cond = ast.branches[0].condition
    assert isinstance(cond.field, FieldAccessNode)
    assert isinstance(cond.value, FieldAccessNode)


def test_choose_inside_each_is_a_parse_error():
    """v2d §102 — `choose` inside `each` is deferred."""
    out = parse_line(
        'each the orders choose if total is above 50: show "big"'
    )
    assert isinstance(out, InscriptResult)
    assert out.status is ResultStatus.ERROR_PARSE
    assert "can't appear inside 'each'" in out.message
    assert "keep" in out.message


def test_choose_missing_if_after_verb_is_a_parse_error():
    out = parse_line('choose score is above 50: show "pass"')
    assert isinstance(out, InscriptResult)
    assert out.status is ResultStatus.ERROR_PARSE


def test_choose_missing_colon_is_a_parse_error():
    out = parse_line('choose if score is above 50 show "pass"')
    assert isinstance(out, InscriptResult)
    assert out.status is ResultStatus.ERROR_PARSE

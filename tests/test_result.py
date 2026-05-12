"""Phase 1 gate tests: structured result objects (v1c §50, v1d §64)."""

from inscript.result import InscriptResult, ResultStatus


def test_all_five_statuses_present():
    names = {s.name for s in ResultStatus}
    assert names == {
        "SUCCESS", "AMBER_PRECEDENCE", "AMBER_AMBIGUITY",
        "ERROR_PARSE", "ERROR_SEMANTIC",
    }


def test_construct_success_with_output():
    r = InscriptResult(
        status=ResultStatus.SUCCESS,
        canonical="show age",
        output=["30"],
        executed=True,
    )
    assert r.status is ResultStatus.SUCCESS
    assert r.output == ["30"]
    assert r.executed is True
    assert r.message is None


def test_construct_amber_precedence():
    r = InscriptResult(
        status=ResultStatus.AMBER_PRECEDENCE,
        canonical="filter the orders where (a and b) or c",
        message="I'll read this as: (A AND B) OR C. Is that what you mean?",
        executed=False,
    )
    assert r.status is ResultStatus.AMBER_PRECEDENCE
    assert r.executed is False
    assert r.message is not None


def test_construct_amber_ambiguity():
    r = InscriptResult(
        status=ResultStatus.AMBER_AMBIGUITY,
        message="I'm not sure if you mean X or Y — can you clarify?",
    )
    assert r.status is ResultStatus.AMBER_AMBIGUITY
    assert r.executed is False


def test_construct_error_parse():
    r = InscriptResult(
        status=ResultStatus.ERROR_PARSE,
        message="I don't recognize a command here.",
    )
    assert r.status is ResultStatus.ERROR_PARSE
    assert r.canonical is None
    assert r.executed is False


def test_construct_error_semantic():
    r = InscriptResult(
        status=ResultStatus.ERROR_SEMANTIC,
        canonical="show missingname",
        message="I can't find 'missingname'.",
    )
    assert r.status is ResultStatus.ERROR_SEMANTIC
    assert r.canonical == "show missingname"
    assert r.executed is False


def test_default_fields():
    r = InscriptResult(status=ResultStatus.SUCCESS)
    assert r.canonical is None
    assert r.output is None
    assert r.message is None
    assert r.executed is False
    assert r.pending_ast is None

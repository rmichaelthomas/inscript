"""Tests for the timer domain pack (src/inscript/packs/timer.py).

The timer pack is the first non-test domain pack — it exercises the
v3a §116–§120 adapter contract with real threading. Intervals in
these tests are kept short (≤50 ms) so the suite stays fast.
"""

from __future__ import annotations

import pytest

from inscript.adapter import LiveValueDeclaration
from inscript.packs.timer import TimerAdapter, TimerDomainPack


# ---------------------------------------------------------------------------
# Declarations
# ---------------------------------------------------------------------------


def test_timer_pack_declares_tick_and_elapsed_as_numbers():
    pack = TimerDomainPack()
    decls = pack.declarations()
    by_name = {d.name: d for d in decls}
    assert set(by_name) == {"tick", "elapsed"}
    assert by_name["tick"] == LiveValueDeclaration(name="tick", value_type="number")
    assert by_name["elapsed"] == LiveValueDeclaration(name="elapsed", value_type="number")


def test_timer_pack_name_defaults_to_timer():
    assert TimerDomainPack().name() == "timer"


def test_timer_adapter_rejects_non_positive_interval():
    with pytest.raises(ValueError) as exc:
        TimerAdapter(interval_ms=0)
    assert "interval_ms" in str(exc.value)


def test_timer_adapter_rejects_negative_max_ticks():
    with pytest.raises(ValueError) as exc:
        TimerAdapter(max_ticks=-1)
    assert "max_ticks" in str(exc.value)


def test_timer_pack_validates_args_at_construction():
    """TimerDomainPack(interval_ms=-1) must fail immediately, not at
    later adapter() time — otherwise the error surfaces far from its
    cause."""
    with pytest.raises(ValueError):
        TimerDomainPack(interval_ms=-1)
    with pytest.raises(ValueError):
        TimerDomainPack(max_ticks=-1)


def test_timer_pack_adapter_is_cached():
    pack = TimerDomainPack()
    a1 = pack.adapter()
    a2 = pack.adapter()
    assert a1 is a2

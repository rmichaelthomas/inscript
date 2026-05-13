"""Tests for the timer domain pack (src/inscript/packs/timer.py).

The timer pack is the first non-test domain pack — it exercises the
v3a §116–§120 adapter contract with real threading. Intervals in
these tests are kept short (≤50 ms) so the suite stays fast.
"""

from __future__ import annotations

import time
from queue import Empty, Queue

import pytest

from inscript.adapter import (
    AdapterDone,
    AdapterUpdate,
    LiveValueDeclaration,
)
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

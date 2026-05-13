"""Timer domain pack — periodic ticks as a live event source.

v3a §116 — declarations + adapter. v3a §119 — single-threaded event
queue (adapter pushes only; never reads). v3a §120 — `stop()` is
interruptible so `finish` and external shutdown don't block on the
sleep interval.

Declarations
------------
- `tick`    — number; increments by 1 every `interval_ms`. Starts at 1
              on the first push (live values are `unset` until the
              first update per v3a §117).
- `elapsed` — number; seconds since adapter start, rounded to 1
              decimal place. Updated on every tick.
"""

from __future__ import annotations

from ..adapter import (
    Adapter,
    DomainPack,
    LiveValueDeclaration,
)


_DEFAULT_INTERVAL_MS = 1000


class TimerAdapter(Adapter):
    """Real adapter implementation — runs on a background thread."""

    def __init__(
        self,
        *,
        interval_ms: int = _DEFAULT_INTERVAL_MS,
        max_ticks: int | None = None,
        name: str = "timer",
    ) -> None:
        super().__init__(name=name)
        if interval_ms <= 0:
            raise ValueError(
                f"TimerAdapter interval_ms must be positive (got {interval_ms})."
            )
        if max_ticks is not None and max_ticks < 0:
            raise ValueError(
                f"TimerAdapter max_ticks must be >= 0 or None (got {max_ticks})."
            )
        self.interval_ms = interval_ms
        self.max_ticks = max_ticks

    def start(self) -> None:
        raise NotImplementedError("filled in by a later task")

    def stop(self) -> None:
        raise NotImplementedError("filled in by a later task")


class TimerDomainPack(DomainPack):
    """DomainPack wrapper around a TimerAdapter."""

    def __init__(
        self,
        *,
        interval_ms: int = _DEFAULT_INTERVAL_MS,
        max_ticks: int | None = None,
        name: str = "timer",
    ) -> None:
        self._name = name
        self._interval_ms = interval_ms
        self._max_ticks = max_ticks
        self._adapter: TimerAdapter | None = None

    def name(self) -> str:
        return self._name

    def declarations(self) -> list[LiveValueDeclaration]:
        return [
            LiveValueDeclaration(name="tick", value_type="number"),
            LiveValueDeclaration(name="elapsed", value_type="number"),
        ]

    def adapter(self) -> Adapter:
        if self._adapter is None:
            self._adapter = TimerAdapter(
                interval_ms=self._interval_ms,
                max_ticks=self._max_ticks,
                name=self._name,
            )
        return self._adapter

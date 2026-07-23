"""Persist every processed event through a pluggable write-ahead log.

Give the bus a ``WAL`` and each completed event is durably recorded. ``JsonlWAL``
writes one JSON object per line to a file; subclass ``WAL`` and implement
``async append(event)`` to send events anywhere else. Awaiting a dispatch
guarantees its event has been written.

Run: python examples/07_write_ahead_log.py
"""

import asyncio
import tempfile
from pathlib import Path

from transitbus import WAL, Event, EventBus, JsonlWAL


class AuditEntry(Event[None]):
    actor: str
    action: str


async def main() -> None:
    # 1) File-backed WAL: one JSON line per event, tagged with its type.
    path = Path(tempfile.gettempdir()) / "transitbus-audit.jsonl"
    path.unlink(missing_ok=True)

    bus = EventBus(name="audit", wal=JsonlWAL(path))
    bus.on(AuditEntry, lambda e: None)  # a WAL records events even with no logic

    await bus.dispatch(AuditEntry(actor="ada", action="login"))
    await bus.dispatch(AuditEntry(actor="ada", action="export-data"))

    print(f"wrote {path}:")
    print(path.read_text(encoding="utf-8").strip())

    # 2) Custom WAL: anything with an async append(event) works.
    class CollectingWAL(WAL):
        def __init__(self) -> None:
            self.events: list[Event] = []

        async def append(self, event: Event) -> None:
            self.events.append(event)

    memory = CollectingWAL()
    bus2 = EventBus(wal=memory)
    bus2.on(AuditEntry, lambda e: None)

    await bus2.dispatch(AuditEntry(actor="bob", action="logout"))
    print(f"\ncustom WAL captured: {[e.action for e in memory.events]}")


if __name__ == "__main__":
    asyncio.run(main())

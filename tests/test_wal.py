import json

from tests.conftest import Ping
from transitbus import WAL, Event, EventBus, JsonlWAL
from transitbus.wal import _serialize


async def test_wal_appends_completed_events(tmp_path) -> None:
    path = tmp_path / "events.jsonl"
    bus = EventBus(wal=JsonlWAL(path))
    bus.on(Ping, lambda e: None)

    await bus.dispatch(Ping(note="one"))
    await bus.dispatch(Ping(note="two"))

    lines = path.read_text(encoding="utf-8").splitlines()
    records = [json.loads(line) for line in lines]
    assert [r["type"] for r in records] == ["Ping", "Ping"]
    assert [r["note"] for r in records] == ["one", "two"]


async def test_custom_wal_subclass() -> None:
    captured: list[Event] = []

    class ListWAL(WAL):
        async def append(self, event: Event) -> None:
            captured.append(event)

    bus = EventBus(wal=ListWAL())
    bus.on(Ping, lambda e: None)
    await bus.dispatch(Ping(note="x"))

    assert captured and isinstance(captured[0], Ping)


def test_serialize_tags_event_type() -> None:
    payload = _serialize(Ping(note="hello"))
    assert payload["type"] == "Ping"
    assert payload["note"] == "hello"
    assert "id" in payload and "created_at" in payload


async def test_wal_appends_only_after_handlers_complete() -> None:
    order: list[str] = []

    class OrderWAL(WAL):
        async def append(self, event: Event) -> None:
            order.append("wal")

    bus = EventBus(wal=OrderWAL())
    bus.on(Ping, lambda e: order.append("handler"))

    await bus.dispatch(Ping(note="x"))

    assert order == ["handler", "wal"]


async def test_wal_failure_does_not_break_dispatch() -> None:
    handled: list[str] = []

    class BrokenWAL(WAL):
        async def append(self, event: Event) -> None:
            raise OSError("disk full")

    bus = EventBus(wal=BrokenWAL())
    bus.on(Ping, lambda e: handled.append(e.note) or "value")

    result = await bus.dispatch(Ping(note="x")).result()

    # handler ran and its value is still retrievable despite the WAL error
    assert handled == ["x"]
    assert result == "value"

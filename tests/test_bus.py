from __future__ import annotations

import asyncio

import pytest

from tests.conftest import ChildEvent, ParentEvent, Ping, Pong
from transitbus import Event, EventBus, HandlerError


async def test_dispatch_runs_matching_handler() -> None:
    bus = EventBus()
    seen: list[str] = []

    bus.on(Ping, lambda e: seen.append(e.note))
    await bus.dispatch(Ping(note="hi"))

    assert seen == ["hi"]


async def test_result_returns_first_value() -> None:
    bus = EventBus()
    bus.on(Ping, lambda e: e.note.upper())

    result = await bus.dispatch(Ping(note="hi")).result()

    assert result == "HI"


async def test_async_and_sync_handlers_both_run() -> None:
    bus = EventBus()

    def sync_handler(event: Ping) -> str:
        return "sync"

    async def async_handler(event: Ping) -> str:
        await asyncio.sleep(0)
        return "async"

    bus.on(Ping, sync_handler)
    bus.on(Ping, async_handler)

    values = await bus.dispatch(Ping()).values()

    assert set(values) == {"sync", "async"}


async def test_subclass_subscription_acts_as_wildcard() -> None:
    bus = EventBus()
    seen: list[str] = []

    bus.on(Event, lambda e: seen.append(type(e).__name__))
    await bus.dispatch(Ping())
    await bus.dispatch(Pong())

    assert seen == ["Ping", "Pong"]


async def test_decorator_and_annotation_subscription() -> None:
    bus = EventBus()
    calls: list[str] = []

    @bus.on(Ping)
    async def on_ping(event: Ping) -> None:
        calls.append("decorator")

    @bus.subscribe
    async def on_pong(event: Pong) -> None:
        calls.append("annotation")

    await bus.dispatch(Ping())
    await bus.dispatch(Pong())

    assert calls == ["decorator", "annotation"]


async def test_handler_failure_surfaces_via_result() -> None:
    bus = EventBus()

    def boom(event: Ping) -> str:
        raise ValueError("nope")

    bus.on(Ping, boom)
    handle = bus.dispatch(Ping())

    with pytest.raises(HandlerError):
        await handle.result()
    # the event still completed, results are inspectable
    results = await handle.results()
    assert results[0].exception is not None


async def test_child_event_gets_parent_id() -> None:
    bus = EventBus()
    children: list[ChildEvent] = []

    async def on_parent(event: ParentEvent) -> None:
        child = await bus.dispatch(ChildEvent(label="c"))
        children.append(child.event)

    bus.on(ParentEvent, on_parent)
    bus.on(ChildEvent, lambda e: None)

    parent = ParentEvent()
    await bus.dispatch(parent)

    assert len(children) == 1
    assert children[0].parent_id == parent.id


async def test_top_level_dispatch_is_fifo() -> None:
    bus = EventBus()
    order: list[int] = []

    async def handler(event: Ping) -> None:
        await asyncio.sleep(0.01 if event.note == "0" else 0)
        order.append(int(event.note))

    bus.on(Ping, handler)

    handles = [bus.dispatch(Ping(note=str(i))) for i in range(5)]
    await asyncio.gather(*handles)

    assert order == [0, 1, 2, 3, 4]


async def test_expect_resolves_on_dispatch() -> None:
    bus = EventBus()

    async def waiter() -> Pong:
        return await bus.expect(Pong, timeout=1)

    task = asyncio.ensure_future(waiter())
    await asyncio.sleep(0)
    bus.dispatch(Pong(note="ready"))

    result = await task
    assert result.note == "ready"


async def test_expect_honours_predicate_and_timeout() -> None:
    bus = EventBus()

    task = asyncio.ensure_future(
        bus.expect(Pong, where=lambda e: e.note == "target", timeout=1)
    )
    await asyncio.sleep(0)
    bus.dispatch(Pong(note="other"))
    bus.dispatch(Pong(note="target"))

    result = await task
    assert result.note == "target"

    with pytest.raises(asyncio.TimeoutError):
        await bus.expect(Pong, timeout=0.05)


async def test_history_records_processed_events() -> None:
    bus = EventBus()
    bus.on(Ping, lambda e: None)

    await bus.dispatch(Ping(note="a"))
    await bus.dispatch(Ping(note="b"))

    notes = [e.note for e in bus.history if isinstance(e, Ping)]
    assert notes == ["a", "b"]

import pytest

from tests.conftest import Ping, Pong
from transitbus import EventBus


async def test_off_stops_a_handler_from_running() -> None:
    bus = EventBus()
    seen: list[str] = []

    def handler(event: Ping) -> None:
        seen.append(event.note)

    bus.on(Ping, handler)
    bus.off(Ping, handler)

    await bus.dispatch(Ping(note="hi"))

    assert seen == []


def test_off_is_a_no_op_for_unknown_handler() -> None:
    bus = EventBus()

    # never registered — must not raise
    bus.off(Ping, lambda e: None)

    assert bus.handler_count == 0


def test_handler_count_tracks_registrations() -> None:
    bus = EventBus()

    def one(event: Ping) -> None: ...
    def two(event: Ping) -> None: ...
    def three(event: Pong) -> None: ...

    bus.on(Ping, one)
    bus.on(Ping, two)
    bus.on(Pong, three)
    assert bus.handler_count == 3

    bus.off(Ping, one)
    assert bus.handler_count == 2


async def test_subscribe_infers_event_type_from_annotation() -> None:
    bus = EventBus()
    seen: list[str] = []

    @bus.subscribe
    async def on_ping(event: Ping) -> None:
        seen.append(event.note)

    await bus.dispatch(Ping(note="hi"))

    assert seen == ["hi"]


def test_subscribe_rejects_handler_without_parameters() -> None:
    bus = EventBus()

    def no_params() -> None: ...

    with pytest.raises(TypeError):
        bus.subscribe(no_params)


def test_subscribe_rejects_non_event_annotation() -> None:
    bus = EventBus()

    def wrong_type(event: str) -> None: ...

    with pytest.raises(TypeError):
        bus.subscribe(wrong_type)


def test_bus_generates_a_name_when_unset() -> None:
    bus = EventBus()

    assert bus.name.startswith("bus-")
    assert EventBus().name != bus.name

import pytest

from tests.conftest import Ping
from transitbus import EventBus, HandlerError


async def test_values_skips_none_returns() -> None:
    bus = EventBus()
    bus.on(Ping, lambda e: None)
    bus.on(Ping, lambda e: "kept")

    values = await bus.dispatch(Ping()).values()

    assert values == ["kept"]


async def test_result_returns_first_non_none_value() -> None:
    bus = EventBus()
    bus.on(Ping, lambda e: None)
    bus.on(Ping, lambda e: "first")
    bus.on(Ping, lambda e: "second")

    result = await bus.dispatch(Ping()).result()

    assert result == "first"


async def test_result_required_raises_when_no_value() -> None:
    bus = EventBus()
    bus.on(Ping, lambda e: None)

    with pytest.raises(LookupError):
        await bus.dispatch(Ping()).result()


async def test_result_optional_returns_none_when_no_value() -> None:
    bus = EventBus()
    bus.on(Ping, lambda e: None)

    assert await bus.dispatch(Ping()).result(required=False) is None


async def test_by_handler_maps_names_to_values() -> None:
    bus = EventBus()

    def upper(event: Ping) -> str:
        return event.note.upper()

    def length(event: Ping) -> int:
        return len(event.note)

    bus.on(Ping, upper)
    bus.on(Ping, length)

    by_handler = await bus.dispatch(Ping(note="hi")).by_handler()

    # keyed by each handler's qualified name
    assert by_handler == {upper.__qualname__: "HI", length.__qualname__: 2}


async def test_values_raises_handler_error_naming_failed_handlers() -> None:
    bus = EventBus()

    def boom(event: Ping) -> str:
        raise ValueError("nope")

    bus.on(Ping, lambda e: "ok")
    bus.on(Ping, boom)

    with pytest.raises(HandlerError) as excinfo:
        await bus.dispatch(Ping()).values()

    assert "boom" in str(excinfo.value)
    assert isinstance(excinfo.value.__cause__, ValueError)


async def test_values_can_ignore_failures() -> None:
    bus = EventBus()

    def boom(event: Ping) -> str:
        raise ValueError("nope")

    bus.on(Ping, lambda e: "ok")
    bus.on(Ping, boom)

    values = await bus.dispatch(Ping()).values(raise_on_error=False)

    assert values == ["ok"]


async def test_results_expose_every_handler_outcome() -> None:
    bus = EventBus()

    def boom(event: Ping) -> str:
        raise ValueError("nope")

    bus.on(Ping, lambda e: "ok")
    bus.on(Ping, boom)

    results = await bus.dispatch(Ping()).results()

    assert [r.ok for r in results] == [True, False]
    assert results[0].value == "ok"
    assert isinstance(results[1].exception, ValueError)


async def test_done_flips_after_completion() -> None:
    bus = EventBus()
    bus.on(Ping, lambda e: None)

    handle = bus.dispatch(Ping())
    assert handle.done is False

    await handle
    assert handle.done is True

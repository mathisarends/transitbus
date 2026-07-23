from tests.conftest import Ping
from transitbus.context import current_event, handling


def test_current_event_is_none_outside_handling() -> None:
    assert current_event() is None


def test_handling_sets_and_restores_current_event() -> None:
    event = Ping()

    with handling(event):
        assert current_event() is event

    assert current_event() is None


def test_handling_restores_previous_event_when_nested() -> None:
    outer = Ping(note="outer")
    inner = Ping(note="inner")

    with handling(outer):
        with handling(inner):
            assert current_event() is inner
        assert current_event() is outer

    assert current_event() is None

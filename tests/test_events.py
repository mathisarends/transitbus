import pytest
from pydantic import ValidationError

from tests.conftest import Ping
from transitbus import HandlerResult


def test_each_event_gets_a_unique_id() -> None:
    assert Ping().id != Ping().id


def test_path_default_is_not_shared_between_events() -> None:
    first = Ping()
    second = Ping()

    first.path.append("main")

    # the forwarding logic relies on each event owning its own path
    assert second.path == []


def test_event_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        Ping(unexpected="value")


def test_event_defaults_are_populated() -> None:
    event = Ping()

    assert isinstance(event.id, str) and event.id
    assert event.parent_id is None
    assert event.path == []
    assert event.created_at.tzinfo is not None


def test_handler_result_ok_reflects_exception() -> None:
    assert HandlerResult(handler="h", value=1).ok is True
    assert HandlerResult(handler="h", exception=ValueError()).ok is False

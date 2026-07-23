from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar

from transitbus.events import Event

_current_event: ContextVar[Event | None] = ContextVar(
    "transitbus_current_event", default=None
)


def current_event() -> Event | None:
    return _current_event.get()


@contextmanager
def handling(event: Event) -> Generator[None]:
    token = _current_event.set(event)
    try:
        yield
    finally:
        _current_event.reset(token)

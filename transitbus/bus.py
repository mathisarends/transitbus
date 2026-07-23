import asyncio
import inspect
import logging
import typing
import uuid
from collections import deque
from collections.abc import Awaitable, Callable
from typing import overload

from transitbus.context import current_event, handling
from transitbus.dispatch import Dispatch
from transitbus.events import Event, HandlerResult
from transitbus.log import EventLog

logger = logging.getLogger(__name__)

type Handler[E: Event] = Callable[[E], Awaitable[object] | object]
type Predicate[E: Event] = Callable[[E], bool]


class _Waiter[E: Event]:
    __slots__ = ("event_type", "future", "where")

    def __init__(
        self,
        event_type: type[E],
        where: Predicate[E] | None,
        future: asyncio.Future[E],
    ) -> None:
        self.event_type = event_type
        self.where = where
        self.future = future

    def matches(self, event: Event) -> bool:
        return isinstance(event, self.event_type) and (
            self.where is None or self.where(event)
        )


class EventBus:
    def __init__(
        self,
        *,
        name: str | None = None,
        log: EventLog | None = None,
        max_history: int | None = 1000,
    ) -> None:
        self.name = name or f"bus-{uuid.uuid4().hex[:8]}"
        self._log = log
        self._handlers: dict[type[Event], list[Handler]] = {}
        self._waiters: list[_Waiter] = []
        self._history: deque[Event] = deque(maxlen=max_history)
        self._tail: Dispatch | None = None

    def __repr__(self) -> str:
        return f"<EventBus {self.name!r} handlers={self.handler_count}>"

    @property
    def handler_count(self) -> int:
        return sum(len(hs) for hs in self._handlers.values())

    @property
    def history(self) -> list[Event]:
        return list(self._history)

    @overload
    def on[E: Event](self, event_type: type[E], handler: Handler[E]) -> Handler[E]: ...
    @overload
    def on[E: Event](
        self, event_type: type[E]
    ) -> Callable[[Handler[E]], Handler[E]]: ...

    def on[E: Event](
        self, event_type: type[E], handler: Handler[E] | None = None
    ) -> Handler[E] | Callable[[Handler[E]], Handler[E]]:
        if handler is None:
            return lambda fn: self.on(event_type, fn)
        self._handlers.setdefault(event_type, []).append(handler)
        return handler

    def subscribe[E: Event](self, handler: Handler[E]) -> Handler[E]:
        self.on(_event_type_from_annotation(handler), handler)
        return handler

    def off[E: Event](self, event_type: type[E], handler: Handler[E]) -> None:
        handlers = self._handlers.get(event_type)
        if handlers and handler in handlers:
            handlers.remove(handler)

    def _handlers_for(self, event: Event) -> list[Handler]:
        matched: list[Handler] = []
        for event_type, handlers in self._handlers.items():
            if isinstance(event, event_type):
                matched.extend(handlers)
        return matched

    def dispatch[T](self, event: Event[T]) -> Dispatch[T]:
        parent = current_event()
        handle: Dispatch[T] = Dispatch(event)

        if parent is None:
            previous, self._tail = self._tail, handle
            asyncio.ensure_future(self._process_after(previous, handle))
        else:
            event.parent_id = parent.id
            asyncio.ensure_future(self._process(handle))

        return handle

    async def _process_after(self, previous: Dispatch | None, handle: Dispatch) -> None:
        if previous is not None:
            await previous.wait()
        await self._process(handle)

    async def _process(self, handle: Dispatch) -> None:
        event = handle.event
        self._history.append(event)
        self._resolve_waiters(event)

        with handling(event):
            results = [await self._run(h, event) for h in self._handlers_for(event)]

        if self._log is not None:
            try:
                await self._log.append(event)
            except Exception:
                logger.exception("event log append failed for %s", type(event).__name__)

        handle._complete(results)

    async def _run(self, handler: Handler, event: Event) -> HandlerResult:
        name = _name_of(handler)
        try:
            outcome = handler(event)
            if inspect.isawaitable(outcome):
                outcome = await outcome
            return HandlerResult(handler=name, value=outcome)
        except Exception as exc:
            logger.exception("handler %s failed for %s", name, type(event).__name__)
            return HandlerResult(handler=name, exception=exc)

    async def expect[E: Event](
        self,
        event_type: type[E],
        *,
        where: Predicate[E] | None = None,
        timeout: float | None = None,
    ) -> E:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[E] = loop.create_future()
        waiter = _Waiter(event_type, where, future)
        self._waiters.append(waiter)
        try:
            return await asyncio.wait_for(future, timeout)
        finally:
            if waiter in self._waiters:
                self._waiters.remove(waiter)

    def _resolve_waiters(self, event: Event) -> None:
        for waiter in list(self._waiters):
            if not waiter.future.done() and waiter.matches(event):
                waiter.future.set_result(event)
                self._waiters.remove(waiter)

    async def idle(self, timeout: float | None = None) -> None:
        if self._tail is not None:
            await self._tail.wait(timeout)


def _name_of(handler: Handler) -> str:
    return getattr(handler, "__qualname__", None) or repr(handler)


def _event_type_from_annotation(handler: Handler) -> type[Event]:
    signature = inspect.signature(handler)
    params = list(signature.parameters.values())
    if not params:
        raise TypeError(f"{_name_of(handler)} takes no event parameter to infer from")

    hints = typing.get_type_hints(handler)
    annotation = hints.get(params[0].name)
    if isinstance(annotation, type) and issubclass(annotation, Event):
        return annotation
    raise TypeError(
        f"Cannot infer event type from {_name_of(handler)}: annotate its first "
        f"parameter with an Event subclass, or use bus.on(EventType, handler)"
    )

# transitbus

A small, type-safe, async event bus for Python. Events are plain
[Pydantic](https://docs.pydantic.dev/) models, handlers subscribe by event
**type**, and the whole thing is a few hundred lines you can read in one sitting.

```python
import asyncio
from transitbus import Event, EventBus


class ComputeSum(Event[int]):
    a: int
    b: int


async def main() -> None:
    bus = EventBus()
    bus.on(ComputeSum, lambda e: e.a + e.b)

    total = await bus.dispatch(ComputeSum(a=100, b=120)).result()
    print(total)  # 220


asyncio.run(main())
```

## Design in one breath

- **Subscribe by type, not by string.** `bus.on(OrderPlaced, handler)` — and
  because matching is structural, a handler on a base class also receives every
  subclass. Subscribing to `Event` observes everything; there is no `'*'`.
- **Lean events.** An `Event` is just data plus `id`, `parent_id`, `created_at`
  and `path`. Results live on the `Dispatch` handle that `dispatch()` returns,
  not bolted onto the event.
- **Automatic causality.** An event dispatched from inside a handler becomes a
  child of the running event, tracked with a `ContextVar` — no globals, no
  wiring by hand.
- **Pluggable write-ahead log.** The bus writes completed events to a `WAL`;
  drop in `JsonlWAL` for a file, or subclass `WAL` for anything else.

## Usage

### Subscribing

```python
# direct
bus.on(OrderPlaced, on_order)

# as a decorator
@bus.on(OrderPlaced)
async def on_order(event: OrderPlaced) -> None: ...

# infer the type from the annotation
@bus.subscribe
async def on_order(event: OrderPlaced) -> None: ...
```

Both `async` and plain `def` handlers work. A handler subscribed to a base
class receives its subclasses too:

```python
bus.on(Event, audit)  # audit() sees every event on the bus
```

### Dispatching and results

`dispatch()` returns immediately with an awaitable `Dispatch` handle:

```python
handle = bus.dispatch(ComputeSum(a=1, b=2))

await handle                     # wait for all handlers, get the handle back
await handle.result()            # first non-None value returned by a handler
await handle.values()            # every non-None value
await handle.by_handler()        # {handler name: value}
await handle.results()           # list[HandlerResult] incl. any exceptions
```

If a handler raises, its exception is captured on the `HandlerResult`; asking
for a `result()`/`values()` re-raises it as `HandlerError` (opt out with
`raise_on_error=False`).

### Parent / child causality

```python
@bus.on(OrderPlaced)
async def charge(event: OrderPlaced) -> None:
    # parent_id is set automatically from the running event
    await bus.dispatch(PaymentCharged(order_id=event.order_id))
```

Top-level dispatches are processed one at a time, in order (FIFO). A child
dispatched from within a handler runs on its own, so awaiting it inside the
handler processes it right away without blocking the queue.

### Waiting for an event

```python
# resolves as soon as a matching event is dispatched
paid = await bus.expect(PaymentCharged, where=lambda e: e.order_id == "A-1", timeout=30)
```

### Forwarding between buses

Because `dispatch` is itself a valid handler, one bus can subscribe to another.
`forward_to` is the readable form of `on(Event, other.dispatch)`:

```python
main.forward_to(auth)
auth.forward_to(data)
data.forward_to(main)  # cycles are fine
```

Each event carries `path` — the names of the buses it has visited. A bus skips
an event it has already seen, so cycles terminate on their own; no handler
introspection involved. Within a bus, more specific subscriptions run first, so
forwarding (a base-`Event` subscription) happens after local handlers.

### Write-ahead log

```python
from transitbus import EventBus, JsonlWAL

bus = EventBus(wal=JsonlWAL("events.jsonl"))
```

Every processed event is appended as one JSON object per line, tagged with its
type. Awaiting a dispatch guarantees its event has been written. Subclass `WAL`
and implement `async append(event)` to write anywhere else.

## Development

```bash
uv sync
uv run pytest
uv run ruff check
```

The [`examples/`](examples/) directory has one runnable script per feature (see
its [README](examples/README.md)); [`examples/orders.py`](examples/orders.py) is
an end-to-end walkthrough.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to install with uv and open a
pull request.

## License

[MIT](LICENSE)

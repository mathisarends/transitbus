"""Many handlers, many results -- and what happens when one raises.

A single event can have several handlers. The ``Dispatch`` handle offers a few
views over their outcomes: every value, a name->value map, or the raw
``HandlerResult`` list (which also carries any exceptions). Asking for values
re-raises a failed handler as ``HandlerError`` unless you opt out.

Run: python examples/03_results_and_errors.py
"""

import asyncio
import logging

from transitbus import Event, EventBus, HandlerError

# The bus logs every handler failure via logging.exception. That is the right
# default in production, but here it would bury the output -- so quiet it and
# let the Dispatch handle be our single source of truth about what failed.
logging.getLogger("transitbus").setLevel(logging.CRITICAL)


class Quote(Event[float]):
    symbol: str


async def main() -> None:
    bus = EventBus()

    @bus.on(Quote)
    def broker_a(event: Quote) -> float:
        return 100.0

    @bus.on(Quote)
    def broker_b(event: Quote) -> float:
        return 101.5

    handle = bus.dispatch(Quote(symbol="ACME"))

    print("values():   ", await handle.values())
    print("result():   ", await handle.result())  # first non-None value
    print("by_handler():", await handle.by_handler())

    # Now a handler that fails alongside one that succeeds.
    @bus.on(Quote)
    def broker_flaky(event: Quote) -> float:
        raise RuntimeError("feed disconnected")

    handle = bus.dispatch(Quote(symbol="ACME"))

    # results() never raises -- inspect each outcome yourself.
    for r in await handle.results():
        status = "ok" if r.ok else f"FAILED ({r.exception})"
        print(f"  {r.handler}: {status}")

    # values(raise_on_error=False) simply drops the failed handler.
    print("survivors:  ", await handle.values(raise_on_error=False))

    # By default a failure surfaces as HandlerError.
    try:
        await bus.dispatch(Quote(symbol="ACME")).values()
    except HandlerError as exc:
        print(f"raised:      {exc}")


if __name__ == "__main__":
    asyncio.run(main())

"""Request/response: dispatch an event, await the value a handler returns.

An ``Event[T]`` declares that handlers produce a ``T``. ``dispatch()`` hands
back a ``Dispatch`` handle; ``.result()`` awaits it and gives you the first
non-None value a handler returned.

Run: python examples/01_request_response.py
"""

import asyncio

from transitbus import Event, EventBus


class ComputeSum(Event[int]):
    a: int
    b: int


class Greet(Event[str]):
    name: str


async def main() -> None:
    bus = EventBus()

    # A handler is just a function of the event. It may be sync or async,
    # and whatever it returns becomes the event's result.
    bus.on(ComputeSum, lambda e: e.a + e.b)

    @bus.on(Greet)
    async def greet(event: Greet) -> str:
        return f"Hello, {event.name}!"

    total = await bus.dispatch(ComputeSum(a=100, b=120)).result()
    print(f"100 + 120 = {total}")

    message = await bus.dispatch(Greet(name="Ada")).result()
    print(message)


if __name__ == "__main__":
    asyncio.run(main())

"""Forward events between buses -- and why cycles are safe.

Because ``dispatch`` is itself a valid handler, one bus can subscribe to another.
``forward_to`` is the readable form of ``on(Event, other.dispatch)``. Each event
records the ``path`` of buses it has visited; a bus ignores an event it has
already seen, so even a cycle terminates on its own.

Run: python examples/06_forwarding.py
"""

import asyncio

from transitbus import Event, EventBus


class Alarm(Event[None]):
    reason: str


async def main() -> None:
    edge = EventBus(name="edge")
    gateway = EventBus(name="gateway")
    cloud = EventBus(name="cloud")

    # A ring: edge -> gateway -> cloud -> edge. The cycle is intentional.
    edge.forward_to(gateway)
    gateway.forward_to(cloud)
    cloud.forward_to(edge)

    gateway.on(Alarm, lambda e: print(f"[gateway] relaying: {e.reason}"))
    cloud.on(Alarm, lambda e: print(f"[cloud]   storing:  {e.reason}"))

    alarm = Alarm(reason="door opened")
    await edge.dispatch(alarm)
    await cloud.idle()  # let the forwarded copies drain

    # The path shows every bus the event visited -- and it stopped, no loop.
    print(f"\npath visited: {alarm.path}")


if __name__ == "__main__":
    asyncio.run(main())

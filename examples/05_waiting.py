"""Wait for an event to appear, without subscribing a handler.

``bus.expect(EventType, where=..., timeout=...)`` resolves as soon as a matching
event is dispatched. Handy for coordinating with work happening elsewhere -- a
sensor, a background task, another coroutine.

Run: python examples/05_waiting.py
"""

import asyncio

from transitbus import Event, EventBus


class SensorReading(Event[None]):
    celsius: float


async def main() -> None:
    bus = EventBus()

    async def sensor() -> None:
        # A background source emitting readings over time.
        for celsius in (18.0, 20.5, 26.3, 24.0):
            await asyncio.sleep(0.05)
            bus.dispatch(SensorReading(celsius=celsius))

    asyncio.create_task(sensor())

    # Block until a reading crosses the threshold (or the timeout fires).
    hot = await bus.expect(SensorReading, where=lambda e: e.celsius > 25, timeout=5)
    print(f"alert: temperature reached {hot.celsius} C")

    # Timeouts raise asyncio.TimeoutError -- nothing above 100 C will arrive.
    try:
        await bus.expect(SensorReading, where=lambda e: e.celsius > 100, timeout=0.3)
    except TimeoutError:
        print("no reading above 100 C within 0.3s (as expected)")


if __name__ == "__main__":
    asyncio.run(main())

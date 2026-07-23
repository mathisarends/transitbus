"""Three ways to subscribe, plus base-class subscriptions that see everything.

Handlers subscribe by event *type*. Because matching walks the class hierarchy,
a handler on a base class also receives every subclass -- subscribe to ``Event``
itself to audit the whole bus.

Run: python examples/02_subscribing.py
"""

import asyncio

from transitbus import Event, EventBus


class UserSignedUp(Event[None]):
    email: str


class UserDeleted(Event[None]):
    email: str


async def main() -> None:
    bus = EventBus()

    # 1) Direct: bus.on(EventType, handler)
    bus.on(UserSignedUp, lambda e: print(f"[direct]   welcome {e.email}"))

    # 2) Decorator: the type is the argument.
    @bus.on(UserDeleted)
    async def on_deleted(event: UserDeleted) -> None:
        print(f"[decorator] goodbye {event.email}")

    # 3) Inferred: bus.subscribe reads the type from the parameter annotation.
    @bus.subscribe
    async def welcome_again(event: UserSignedUp) -> None:
        print(f"[inferred]  say hi to {event.email}")

    # Subscribing to the base Event observes *every* event on the bus.
    @bus.on(Event)
    async def audit(event: Event) -> None:
        print(f"[audit]     {type(event).__name__}")

    await bus.dispatch(UserSignedUp(email="ada@example.com"))
    await bus.dispatch(UserDeleted(email="ada@example.com"))

    print(f"\nhandlers registered: {bus.handler_count}")


if __name__ == "__main__":
    asyncio.run(main())

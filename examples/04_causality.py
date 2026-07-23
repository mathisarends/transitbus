"""Automatic parent/child causality between events.

When you dispatch an event from *inside* a handler, transitbus links it to the
event currently being handled: the child's ``parent_id`` is set to the parent's
``id`` automatically, tracked through a ContextVar -- no wiring by hand.

Run: python examples/04_causality.py
"""

import asyncio

from transitbus import Event, EventBus


class OrderPlaced(Event[None]):
    order_id: str
    total: float


class PaymentCharged(Event[None]):
    order_id: str
    amount: float


class ReceiptEmailed(Event[None]):
    order_id: str


async def main() -> None:
    bus = EventBus()

    @bus.on(OrderPlaced)
    async def charge(event: OrderPlaced) -> None:
        # Dispatched from within a handler -> becomes a child of OrderPlaced.
        await bus.dispatch(PaymentCharged(order_id=event.order_id, amount=event.total))

    @bus.on(PaymentCharged)
    async def email_receipt(event: PaymentCharged) -> None:
        # And this one becomes a child of PaymentCharged.
        await bus.dispatch(ReceiptEmailed(order_id=event.order_id))

    placed = await bus.dispatch(OrderPlaced(order_id="A-1", total=42.0))
    await bus.idle()  # let the chain of children settle

    # Reconstruct the causal chain from history via parent_id links.
    by_id = {e.id: e for e in bus.history}
    print("causal chain (parent -> child):")
    for event in bus.history:
        parent = by_id.get(event.parent_id) if event.parent_id else None
        arrow = f"  {type(parent).__name__} -> " if parent else "  (root) "
        print(f"{arrow}{type(event).__name__}")

    charged = next(e for e in bus.history if isinstance(e, PaymentCharged))
    print(
        f"\nPaymentCharged.parent_id == OrderPlaced.id: "
        f"{charged.parent_id == placed.event.id}"
    )


if __name__ == "__main__":
    asyncio.run(main())

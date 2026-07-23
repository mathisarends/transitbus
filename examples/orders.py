import asyncio
import tempfile
from pathlib import Path

from transitbus import Event, EventBus, JsonlWAL


class OrderPlaced(Event[None]):
    order_id: str
    total: float


class PaymentCharged(Event[str]):
    order_id: str
    amount: float


async def main() -> None:
    wal = Path(tempfile.gettempdir()) / "transitbus-orders.jsonl"
    wal.unlink(missing_ok=True)
    bus = EventBus(name="orders", wal=JsonlWAL(wal))

    @bus.on(OrderPlaced)
    async def charge_card(event: OrderPlaced) -> None:
        await bus.dispatch(PaymentCharged(order_id=event.order_id, amount=event.total))

    @bus.subscribe
    async def confirm(event: PaymentCharged) -> str:
        return f"charged ${event.amount:.2f} for {event.order_id}"

    placed = OrderPlaced(order_id="A-1", total=42.0)
    await bus.dispatch(placed)
    await bus.idle()

    charged = next(e for e in bus.history if isinstance(e, PaymentCharged))
    print(f"parent_id links back to order: {charged.parent_id == placed.id}")
    print(wal.read_text(encoding="utf-8").strip())


if __name__ == "__main__":
    asyncio.run(main())

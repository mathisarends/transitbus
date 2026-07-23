from tests.conftest import ChildEvent, Ping
from transitbus import EventBus


async def test_event_propagates_across_buses() -> None:
    main = EventBus(name="main")
    auth = EventBus(name="auth")
    data = EventBus(name="data")

    main.forward_to(auth)
    auth.forward_to(data)
    data.forward_to(main)

    seen: list[str] = []
    auth.on(Ping, lambda e: seen.append("auth"))
    data.on(Ping, lambda e: seen.append("data"))

    event = Ping(note="x")
    await main.dispatch(event)

    assert seen == ["auth", "data"]
    assert event.path == ["main", "auth", "data"]
    assert event.parent_id is None


async def test_loop_is_prevented() -> None:
    a = EventBus(name="a")
    b = EventBus(name="b")
    a.forward_to(b)
    b.forward_to(a)

    hits: list[str] = []
    a.on(Ping, lambda e: hits.append("a"))
    b.on(Ping, lambda e: hits.append("b"))

    event = Ping(note="x")
    await a.dispatch(event)

    assert hits == ["a", "b"]
    assert event.path == ["a", "b"]


async def test_diamond_reaches_shared_sink_once() -> None:
    top = EventBus(name="top")
    left = EventBus(name="left")
    right = EventBus(name="right")
    sink = EventBus(name="sink")

    top.forward_to(left)
    top.forward_to(right)
    left.forward_to(sink)
    right.forward_to(sink)

    hits: list[str] = []
    for bus in (left, right, sink):
        bus.on(Ping, lambda e, name=bus.name: hits.append(name))

    event = Ping(note="x")
    await top.dispatch(event)

    assert hits.count("sink") == 1
    assert sorted(hits) == ["left", "right", "sink"]
    assert event.path == ["top", "left", "sink", "right"]


async def test_child_in_forwarded_handler_parents_to_the_event() -> None:
    a = EventBus(name="a")
    b = EventBus(name="b")
    a.forward_to(b)

    children: list[ChildEvent] = []

    async def on_ping(event: Ping) -> None:
        child = await b.dispatch(ChildEvent(label="c"))
        children.append(child.event)

    b.on(Ping, on_ping)
    b.on(ChildEvent, lambda e: None)

    event = Ping(note="x")
    await a.dispatch(event)

    assert len(children) == 1
    assert children[0].parent_id == event.id
    assert children[0].parent_id != children[0].id

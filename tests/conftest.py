from transitbus import Event


class Ping(Event[str]):
    note: str = ""


class Pong(Event[str]):
    note: str = ""


class ParentEvent(Event):
    pass


class ChildEvent(Event):
    label: str

import asyncio
import json
from abc import ABC, abstractmethod
from pathlib import Path

from transitbus.events import Event


class WAL(ABC):
    @abstractmethod
    async def append(self, event: Event) -> None: ...


def _serialize(event: Event) -> dict[str, object]:
    return {"type": type(event).__name__, **event.model_dump(mode="json")}


class JsonlWAL(WAL):
    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()

    async def append(self, event: Event) -> None:
        line = json.dumps(_serialize(event))
        async with self._lock:
            await asyncio.to_thread(self._write, line)

    def _write(self, line: str) -> None:
        with self._path.open("a", encoding="utf-8") as file:
            file.write(line + "\n")

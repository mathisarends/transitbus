import asyncio
from collections.abc import Generator

from transitbus.events import Event, HandlerResult


class HandlerError(Exception):
    def __init__(self, results: list[HandlerResult]) -> None:
        self.results = results
        failed = [r for r in results if not r.ok]
        names = ", ".join(r.handler for r in failed)
        super().__init__(f"{len(failed)} handler(s) failed: {names}")
        self.__cause__ = failed[0].exception if failed else None


class Dispatch[TResult]:
    def __init__(self, event: Event[TResult]) -> None:
        self.event = event
        self._finished = asyncio.Event()
        self._results: list[HandlerResult] = []

    def __repr__(self) -> str:
        state = "done" if self.done else "pending"
        return f"<Dispatch {type(self.event).__name__} {state}>"

    @property
    def done(self) -> bool:
        return self._finished.is_set()

    def _complete(self, results: list[HandlerResult]) -> None:
        self._results = results
        self._finished.set()

    async def wait(self, timeout: float | None = None) -> "Dispatch[TResult]":
        await asyncio.wait_for(self._finished.wait(), timeout)
        return self

    def __await__(self) -> Generator[object, None, "Dispatch[TResult]"]:
        return self.wait().__await__()

    async def results(self) -> list[HandlerResult]:
        await self._finished.wait()
        return list(self._results)

    async def values(self, *, raise_on_error: bool = True) -> list[TResult]:
        results = await self.results()
        if raise_on_error and any(not r.ok for r in results):
            raise HandlerError(results)
        return [r.value for r in results if r.ok and r.value is not None]

    async def result(
        self, *, raise_on_error: bool = True, required: bool = True
    ) -> TResult | None:
        values = await self.values(raise_on_error=raise_on_error)
        if values:
            return values[0]
        if required:
            raise LookupError(
                f"No handler returned a value for {type(self.event).__name__}"
            )
        return None

    async def by_handler(self, *, raise_on_error: bool = True) -> dict[str, TResult]:
        results = await self.results()
        if raise_on_error and any(not r.ok for r in results):
            raise HandlerError(results)
        return {r.handler: r.value for r in results if r.ok and r.value is not None}

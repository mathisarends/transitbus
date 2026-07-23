import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _new_id() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(UTC)


class Event[TResult](BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=_new_id)
    parent_id: str | None = None
    created_at: datetime = Field(default_factory=_now)
    path: list[str] = Field(default_factory=list)


@dataclass(slots=True, frozen=True)
class HandlerResult:
    handler: str
    value: Any = None
    exception: BaseException | None = None

    @property
    def ok(self) -> bool:
        return self.exception is None

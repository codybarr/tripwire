from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Observation:
    status: str
    summary: str
    url: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Event:
    monitor_id: str
    monitor_name: str
    status: str
    previous_status: str | None
    occurred_at: str
    summary: str
    url: str | None
    attributes: dict[str, Any]

    @property
    def id(self) -> str:
        return f"{self.status}:{self.occurred_at}"

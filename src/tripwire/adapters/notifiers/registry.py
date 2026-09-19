from __future__ import annotations

from typing import Any, Protocol

from ...domain.models import Event
from ...errors import TripwireError
from .ntfy import NtfyNotifier


class Notifier(Protocol):
    def deliver(self, config: dict[str, Any], event: Event, dry_run: bool) -> None: ...


BUILTIN_NOTIFIERS: dict[str, Notifier] = {"ntfy": NtfyNotifier()}


def deliver(config: dict[str, Any], event: Event, dry_run: bool) -> None:
    notifier_type = config["type"]
    notifier = BUILTIN_NOTIFIERS.get(notifier_type)
    if notifier is None:
        raise TripwireError(f"unsupported notifier type {notifier_type!r}")
    notifier.deliver(config, event, dry_run)

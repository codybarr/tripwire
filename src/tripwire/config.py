from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .errors import TripwireError


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise TripwireError(f"could not read {path}: {error}") from error
    if not isinstance(value, dict):
        raise TripwireError("config root must be an object")
    validate(value)
    return value


def require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TripwireError(f"{label} must be an object")
    return value


def require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TripwireError(f"{label} must be a non-empty string")
    return value


def require_url(value: Any, label: str) -> str:
    url = require_string(value, label)
    if urlparse(url).scheme not in {"http", "https"}:
        raise TripwireError(f"{label} must be an HTTP(S) URL")
    return url


def validate_probe(spec: dict[str, Any], label: str) -> None:
    probe_type = require_string(spec.get("type"), f"{label}.type")
    require_url(spec.get("url"), f"{label}.url")
    requirements = {
        "http.json": ("path", "equals"),
        "woocommerce.variation": ("attribute", "value"),
        "laudisi.product_cards": ("name_contains_any",),
    }
    if probe_type not in requirements:
        raise TripwireError(f"{label}.type {probe_type!r} is not supported")
    for key in requirements[probe_type]:
        if key not in spec:
            raise TripwireError(f"{label}.{key} is required")
    if probe_type == "http.json":
        require_string(spec["path"], f"{label}.path")
    if probe_type == "woocommerce.variation":
        require_string(spec["attribute"], f"{label}.attribute")
        require_string(spec["value"], f"{label}.value")
    if probe_type == "laudisi.product_cards":
        needles = spec["name_contains_any"]
        if not isinstance(needles, list) or not needles or not all(isinstance(item, str) and item for item in needles):
            raise TripwireError(f"{label}.name_contains_any must be a non-empty list of strings")


def validate(config: dict[str, Any]) -> None:
    if config.get("version") != 1:
        raise TripwireError("config.version must be 1")
    notifiers = require_object(config.get("notifiers"), "config.notifiers")
    for notifier_id, notifier in notifiers.items():
        notifier = require_object(notifier, f"notifiers.{notifier_id}")
        if require_string(notifier.get("type"), f"notifiers.{notifier_id}.type") != "ntfy":
            raise TripwireError(f"notifiers.{notifier_id}: unsupported notifier type")
        require_string(notifier.get("topic_env"), f"notifiers.{notifier_id}.topic_env")

    monitors = config.get("monitors")
    if not isinstance(monitors, list):
        raise TripwireError("config.monitors must be a list")
    ids: set[str] = set()
    for index, monitor_value in enumerate(monitors):
        label = f"monitors[{index}]"
        monitor = require_object(monitor_value, label)
        monitor_id = require_string(monitor.get("id"), f"{label}.id")
        if monitor_id in ids:
            raise TripwireError(f"duplicate monitor id {monitor_id!r}")
        ids.add(monitor_id)
        require_string(monitor.get("name"), f"{label}.name")
        if "enabled" in monitor and not isinstance(monitor["enabled"], bool):
            raise TripwireError(f"{label}.enabled must be a boolean")
        validate_probe(require_object(monitor.get("probe"), f"{label}.probe"), f"{label}.probe")
        notify = require_object(monitor.get("notify"), f"{label}.notify")
        events = notify.get("on")
        targets = notify.get("notifiers")
        if not isinstance(events, list) or not events or not all(isinstance(item, str) and item for item in events):
            raise TripwireError(f"{label}.notify.on must be a non-empty list of statuses")
        if not isinstance(targets, list) or not targets or not all(isinstance(item, str) and item for item in targets):
            raise TripwireError(f"{label}.notify.notifiers must be a non-empty list")
        unknown = set(targets) - set(notifiers)
        if unknown:
            raise TripwireError(f"{label} references unknown notifiers: {', '.join(sorted(unknown))}")

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .errors import TripwireError

DEFAULT_STATE: dict[str, Any] = {"version": 2, "monitors": {}}


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": 2, "monitors": {}}
    try:
        state = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise TripwireError(f"could not read {path}: {error}") from error
    if not isinstance(state, dict) or not isinstance(state.get("monitors"), dict):
        raise TripwireError("state must contain a monitors object")
    # Version 1 only stored a boolean. Preserve it during the transparent migration.
    if state.get("version") == 1:
        for record in state["monitors"].values():
            if isinstance(record, dict) and isinstance(record.get("available"), bool):
                record["status"] = "available" if record.pop("available") else "unavailable"
        state["version"] = 2
    if state.get("version") != 2:
        raise TripwireError("unsupported state version")
    return state


def write_atomic(path: Path, state: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as output:
            output.write(json.dumps(state, indent=2) + "\n")
            temporary_path = Path(output.name)
        os.replace(temporary_path, path)
    except OSError as error:
        raise TripwireError(f"could not write {path}: {error}") from error

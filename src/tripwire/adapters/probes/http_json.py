from __future__ import annotations

import json
from typing import Any

from ...domain.models import Observation
from ...errors import TripwireError
from ...http import HttpClient


def select(value: Any, path: str) -> Any:
    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
            value = value[int(part)]
        else:
            raise TripwireError(f"JSON path {path!r} was not found")
    return value


class HttpJsonProbe:
    """Compare a value in a JSON response without executable config expressions."""

    def observe(self, spec: dict[str, Any], http: HttpClient) -> Observation:
        url = spec["url"]
        try:
            payload = json.loads(http.get_text(url))
        except json.JSONDecodeError as error:
            raise TripwireError("HTTP response was not valid JSON") from error
        actual = select(payload, spec["path"])
        matches = actual == spec["equals"]
        status = spec.get("status_when_match", "available") if matches else spec.get(
            "status_when_no_match", "unavailable"
        )
        return Observation(str(status), f"JSON {spec['path']} is {actual!r}", url, {"value": actual})

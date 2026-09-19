from __future__ import annotations

import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from ...domain.models import Event
from ...errors import TripwireError


def render(template: str, event: Event) -> str:
    values = {
        "monitor_id": event.monitor_id,
        "monitor_name": event.monitor_name,
        "status": event.status,
        "previous_status": event.previous_status or "unknown",
        "summary": event.summary,
        "url": event.url or "",
    }
    try:
        return template.format(**values)
    except KeyError as error:
        raise TripwireError(f"unknown notification template field {error.args[0]!r}") from error


class NtfyNotifier:
    def deliver(self, config: dict[str, Any], event: Event, dry_run: bool) -> None:
        topic_env = config["topic_env"]
        title = render(config.get("title_template", "Tripwire: {monitor_name} is {status}"), event)
        message = render(config.get("message_template", "{summary}\n{url}"), event)
        if dry_run:
            print(f"[dry run] would send ntfy notification: {title}")
            return
        topic = os.environ.get(topic_env)
        if not topic:
            raise TripwireError(f"notification secret {topic_env} is not configured")
        headers = {"Title": title, "Priority": str(config.get("priority", "default"))}
        tags = config.get("tags")
        if tags:
            headers["Tags"] = ",".join(tags)
        request = urllib.request.Request(
            f"https://ntfy.sh/{urllib.parse.quote(topic, safe='')}",
            data=message.encode("utf-8"),
            method="POST",
            headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status != 200:
                    raise TripwireError(f"ntfy returned HTTP {response.status}")
        except urllib.error.URLError as error:
            raise TripwireError(f"could not send ntfy notification: {error}") from error

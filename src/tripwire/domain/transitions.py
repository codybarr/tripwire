from __future__ import annotations

from .models import Event, Observation


def event_for(
    monitor: dict[str, object], observation: Observation, previous_status: str | None, occurred_at: str
) -> Event | None:
    """Create an event only for an initial known state or a real state transition."""
    if observation.status == "unknown" or observation.status == previous_status:
        return None
    return Event(
        monitor_id=str(monitor["id"]),
        monitor_name=str(monitor["name"]),
        status=observation.status,
        previous_status=previous_status,
        occurred_at=occurred_at,
        summary=observation.summary,
        url=observation.url,
        attributes=observation.attributes,
    )

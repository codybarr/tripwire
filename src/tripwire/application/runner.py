from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..adapters.notifiers.registry import deliver
from ..adapters.probes.registry import observe
from ..domain.models import Event, Observation
from ..domain.transitions import event_for
from ..errors import TripwireError
from ..http import HttpClient


def timestamp() -> str:
    return datetime.now(UTC).isoformat()


def saved_event(monitor: dict[str, Any], record: dict[str, Any], observation: Observation) -> Event | None:
    """Recreate the current event so failed notifier deliveries can be retried."""
    changed_at = record.get("changed_at")
    status = record.get("status")
    if not isinstance(changed_at, str) or status != observation.status:
        return None
    return Event(
        monitor_id=monitor["id"],
        monitor_name=monitor["name"],
        status=status,
        previous_status=record.get("previous_status"),
        occurred_at=changed_at,
        summary=observation.summary,
        url=observation.url,
        attributes=observation.attributes,
    )


def run(config: dict[str, Any], state: dict[str, Any], dry_run: bool = False) -> int:
    """Run enabled monitors, update state in memory, and return a shell exit code."""
    http = HttpClient()
    failures: list[str] = []
    records = state["monitors"]
    notifiers = config["notifiers"]

    for monitor in config["monitors"]:
        monitor_id = monitor["id"]
        if not monitor.get("enabled", True):
            print(f"SKIP  {monitor_id} (disabled)")
            continue
        try:
            observation = observe(monitor["probe"], http)
            existing = records.get(monitor_id, {})
            record = existing if isinstance(existing, dict) else {}
            previous = record.get("status") if isinstance(record.get("status"), str) else None

            if observation.status == "unknown":
                record["last_unknown_at"] = timestamp()
                record["last_error"] = observation.summary
                records[monitor_id] = record
                print(f"OK    {monitor_id}: unknown")
                continue

            observed_at = timestamp()
            event = event_for(monitor, observation, previous, observed_at)
            if event is not None:
                record.update(
                    {
                        "status": observation.status,
                        "previous_status": previous,
                        "changed_at": observed_at,
                    }
                )
            else:
                event = saved_event(monitor, record, observation)
            record.update(
                {
                    "last_success_at": observed_at,
                    "last_summary": observation.summary,
                    "last_url": observation.url,
                    "consecutive_failures": 0,
                }
            )
            records[monitor_id] = record

            delivered = record.setdefault("deliveries", {})
            should_notify = event is not None and event.status in monitor["notify"]["on"]
            sent_any = False
            if should_notify:
                event_deliveries = delivered.setdefault(event.id, {})
                for notifier_id in monitor["notify"]["notifiers"]:
                    if notifier_id in event_deliveries:
                        continue
                    try:
                        deliver(notifiers[notifier_id], event, dry_run)
                        if not dry_run:
                            event_deliveries[notifier_id] = observed_at
                        sent_any = True
                    except TripwireError as error:
                        failures.append(f"{monitor_id} → {notifier_id}: {error}")
                        print(f"ERROR {monitor_id} → {notifier_id}: {error}")
            result = "ALERT" if sent_any else "OK"
            print(f"{result:<5} {monitor_id}: {observation.status}")
        except TripwireError as error:
            record = records.setdefault(monitor_id, {})
            record["consecutive_failures"] = int(record.get("consecutive_failures", 0)) + 1
            record["last_error"] = str(error)
            record["last_failure_at"] = timestamp()
            failures.append(f"{monitor_id}: {error}")
            print(f"ERROR {monitor_id}: {error}")
    return 1 if failures else 0

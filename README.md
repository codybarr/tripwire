# Tripwire

Tripwire is a dependency-free, configuration-driven change detector that runs on GitHub Actions and sends transition-based notifications through [ntfy](https://ntfy.sh). It has no built-in product model: probes observe a named status, the core detects status changes, and notifiers deliver the resulting event.

## Setup

1. Install the **ntfy** app (iOS/Android) or visit [ntfy.sh](https://ntfy.sh).
2. Create and subscribe to a private random topic:
   ```bash
   echo "tripwire-$(uuidgen | tr '[:upper:]' '[:lower:]')"
   ```
3. Add it as the `NTFY_TOPIC` repository secret under **Settings → Secrets and variables → Actions**.
4. In **Settings → Actions → General**, grant the workflow **Read and write permissions**. Tripwire commits `state.json` so it can detect transitions.
5. Enable Actions and run **Check monitors** once.

The scheduled workflow runs hourly. GitHub may delay scheduled jobs during high load.

## Configuration

All configuration is in [`config/monitors.json`](config/monitors.json). It contains three independent parts:

- **notifiers**: destinations for events;
- **monitors**: named things to observe;
- **probe**: the mechanism used to produce a status.

```json
{
  "version": 1,
  "notifiers": {
    "personal-ntfy": {
      "type": "ntfy",
      "topic_env": "NTFY_TOPIC"
    }
  },
  "monitors": [
    {
      "id": "example-api",
      "name": "Example API",
      "enabled": true,
      "probe": {
        "type": "http.json",
        "url": "https://status.example.com/status.json",
        "path": "services.checkout.available",
        "equals": true
      },
      "notify": {
        "on": ["available"],
        "notifiers": ["personal-ntfy"]
      }
    }
  ]
}
```

### Built-in probes

| Type | Purpose | Required probe fields |
| --- | --- | --- |
| `http.json` | Compares a JSON value at a dot-separated path | `url`, `path`, `equals` |
| `woocommerce.variation` | Checks an embedded WooCommerce variation | `url`, `attribute`, `value` |
| `laudisi.product_cards` | Checks selected Laudisi product cards | `url`, `name_contains_any` |

`http.json` returns `available` when the selected value equals `equals`, otherwise `unavailable`. Override those names with `status_when_match` and `status_when_no_match` when another status vocabulary fits better.

The two retailer probes are integrations, not application logic. New probe types belong under `src/tripwire/adapters/probes/` and are registered in `registry.py`; the runner only consumes `Observation` objects.

### Notifications

The current built-in notifier is `ntfy`. It accepts `topic_env`, plus optional `priority`, `tags`, `title_template`, and `message_template`. Templates may use `{monitor_id}`, `{monitor_name}`, `{status}`, `{previous_status}`, `{summary}`, and `{url}`.

A monitor’s `notify.on` is a list of statuses that produce events. For example, `"on": ["available"]` alerts only when a monitor first becomes or returns to available. Set `enabled` to `false` to skip a monitor without making a network request.

## State and alert behavior

- The first successful observation is a status event; it notifies only if its status appears in `notify.on`.
- Later notifications occur only after a status transition.
- Failed probe requests preserve the prior status and are recorded separately.
- Delivery is tracked per notifier and event, so a notifier failure retries without duplicating deliveries that already succeeded.
- `state.json` is automated state. Tripwire transparently migrates the prior version-1 boolean state format to version 2.

## Local commands

No packages are required:

```bash
python3 src/tripwire.py validate
export NTFY_TOPIC='your-ntfy-topic'
python3 src/tripwire.py --dry-run
python3 src/tripwire.py
```

`validate` checks configuration without fetching or notifying. `--dry-run` fetches and evaluates monitors but neither sends notifications nor writes state.

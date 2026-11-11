# tripwire

Loads web pages hourly in a headless browser ([`Bun.WebView`](https://bun.com/docs/runtime/webview)) on GitHub Actions and sends an [ntfy](https://ntfy.sh) notification when something comes back in stock.

## Setup

1. Pick a hard-to-guess ntfy topic and subscribe to it in the ntfy app. Anyone who knows a topic name on ntfy.sh can read it.
2. Push this repo to GitHub and add the topic as the `NTFY_TOPIC` repository secret.
3. Trigger the `check` workflow once by hand to confirm it runs.

Optional: the `NTFY_TOKEN` secret for protected topics, and the `NTFY_SERVER` variable for a self-hosted server.

## Adding a check

Add an entry to `checks.ts`:

```ts
{
  id: "unique-id",
  title: "Shown in the notification",
  url: "https://example.com/product",
  detect: schemaOrgOffer,
}
```

- `schemaOrgOffer` reads the schema.org Product data most stores publish. On multi-variant pages, `url` must exactly match the variant's offer URL.
- `textMatch({ available: /add to cart/i, unavailable: /sold out/i })` is for pages without that data.

A detector is a plain function from a page snapshot to `"available"`, `"unavailable"`, or `"unknown"`, so you can write your own.

## Behavior

- A notification is sent when a check becomes available and wasn't before, including the first time a check runs.
- `unknown` results, such as a blocked page, never notify. They leave saved state alone and fail the run, so GitHub flags them.
- State lives in `state/status.json`, committed by the workflow only when a status changes.
- GitHub can start scheduled runs late, and it disables schedules after 60 days without repository activity on public repos.

## Local use

```sh
bun install
bun test
bun run check --dry-run   # prints instead of notifying, and saves no state
```

Needs Chrome, Chromium, Edge, or Brave installed.

import type { Availability, Detector } from "./detectors";
import type { Notify } from "./ntfy";

export type Check = { id: string; title: string; url: string; detect: Detector };
export type Status = Exclude<Availability, "unknown">;
export type State = Record<string, { status: Status; changedAt: string }>;
export type Observe = (url: string, detect: Detector) => Promise<Availability>;

/**
 * Runs every check and returns the next state. Notifies only on a transition
 * into "available". An inconclusive check or failed notification leaves that
 * check's state alone, so a blocked page can't fake a restock and a lost
 * notification is retried on the next run.
 */
export async function runChecks({
  checks,
  observe,
  notify,
  state,
  now = () => new Date(),
}: {
  checks: Check[];
  observe: Observe;
  notify: Notify;
  state: State;
  now?: () => Date;
}): Promise<{ state: State; failed: string[] }> {
  const next = { ...state };
  const failed: string[] = [];

  for (const check of checks) {
    try {
      const status = await observe(check.url, check.detect);
      console.log(`${check.id}: ${status}`);
      if (status === "unknown") {
        failed.push(check.id);
        continue;
      }
      if (status === state[check.id]?.status) continue;

      if (status === "available") {
        await notify({ title: "Back in stock", message: `${check.title} is available.`, click: check.url });
      }
      next[check.id] = { status, changedAt: now().toISOString() };
    } catch (error) {
      console.error(`${check.id}: ${error}`);
      failed.push(check.id);
    }
  }

  return { state: next, failed };
}

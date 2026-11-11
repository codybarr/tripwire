import { expect, mock, test } from "bun:test";
import type { Availability } from "./detectors";
import type { Notification } from "./ntfy";
import { runChecks, type Check, type State } from "./run";

const check: Check = { id: "item", title: "Item", url: "https://shop.test/item", detect: () => "unknown" };
const now = () => new Date("2026-11-10T00:00:00Z");
const entry = (status: "available" | "unavailable") => ({ status, changedAt: "2026-01-01T00:00:00.000Z" });

async function run(result: Availability | Error, state: State, notifyError?: Error) {
  const notify = mock(async (_: Notification) => {
    if (notifyError) throw notifyError;
  });
  const observe = async () => {
    if (result instanceof Error) throw result;
    return result;
  };
  return { notify, ...(await runChecks({ checks: [check], observe, notify, state, now })) };
}

test("notifies on a restock", async () => {
  const { notify, state, failed } = await run("available", { item: entry("unavailable") });
  expect(notify).toHaveBeenCalledTimes(1);
  expect(notify.mock.calls[0]![0].click).toBe(check.url);
  expect(state.item).toEqual({ status: "available", changedAt: now().toISOString() });
  expect(failed).toEqual([]);
});

test("does not notify again while still in stock", async () => {
  const before = { item: entry("available") };
  const { notify, state } = await run("available", before);
  expect(notify).not.toHaveBeenCalled();
  expect(state).toEqual(before);
});

test("records going out of stock silently", async () => {
  const { notify, state } = await run("unavailable", { item: entry("available") });
  expect(notify).not.toHaveBeenCalled();
  expect(state.item?.status).toBe("unavailable");
});

test("an inconclusive check keeps state, stays silent, and is reported", async () => {
  const before = { item: entry("unavailable") };
  const { notify, state, failed } = await run("unknown", before);
  expect(notify).not.toHaveBeenCalled();
  expect(state).toEqual(before);
  expect(failed).toEqual(["item"]);
});

test("a browser error is reported as a failure", async () => {
  const { failed } = await run(new Error("crashed"), {});
  expect(failed).toEqual(["item"]);
});

test("a failed notification keeps state so the next run retries", async () => {
  const before = { item: entry("unavailable") };
  const { state, failed } = await run("available", before, new Error("ntfy down"));
  expect(state).toEqual(before);
  expect(failed).toEqual(["item"]);
});

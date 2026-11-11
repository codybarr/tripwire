import { checks } from "../checks";
import { observe } from "./browser";
import { createNtfy, type Notify } from "./ntfy";
import { runChecks, type State } from "./run";

const STATE_PATH = `${import.meta.dir}/../state/status.json`;
const dryRun = process.argv.includes("--dry-run");

function createNotifier(): Notify {
  if (dryRun) return async (notification) => console.log("[dry run] would notify:", notification);

  const topic = process.env.NTFY_TOPIC;
  if (!topic) throw new Error("NTFY_TOPIC is not set");
  return createNtfy({
    topic,
    server: process.env.NTFY_SERVER || undefined,
    token: process.env.NTFY_TOKEN || undefined,
  });
}

const notify = createNotifier();
const stateFile = Bun.file(STATE_PATH);
const state: State = (await stateFile.exists()) ? await stateFile.json() : {};

const result = await runChecks({ checks, observe, notify, state });

if (!dryRun) await Bun.write(STATE_PATH, `${JSON.stringify(result.state, null, 2)}\n`);

if (result.failed.length > 0) {
  console.error(`Inconclusive: ${result.failed.join(", ")}`);
  process.exit(1);
}
process.exit(0);

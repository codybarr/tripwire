import type { Availability, Detector, PageSnapshot } from "./detectors";

const SNAPSHOT_SCRIPT = `JSON.stringify({
  url: location.href,
  title: document.title,
  text: document.body ? document.body.innerText : "",
  jsonLd: [...document.querySelectorAll('script[type="application/ld+json"]')].map((s) => s.textContent),
})`;

/**
 * Loads a page and polls until the detector reaches a verdict or time runs out.
 * Polling covers client-rendered content and interstitials that reload the page.
 */
export async function observe(
  url: string,
  detect: Detector,
  { timeoutMs = 45_000, pollMs = 2_000 } = {},
): Promise<Availability> {
  // url: false always spawns a fresh Chrome instead of attaching to one already running.
  await using view = new Bun.WebView({
    backend: { type: "chrome", url: false },
    width: 1280,
    height: 900,
  });
  await view.navigate(url);

  const deadline = Date.now() + timeoutMs;
  let lastTitle = "";
  while (Date.now() < deadline) {
    try {
      const page = JSON.parse((await view.evaluate(SNAPSHOT_SCRIPT)) as string) as PageSnapshot;
      lastTitle = page.title;
      const availability = detect(page, url);
      if (availability !== "unknown") return availability;
    } catch {
      // The page navigated mid-evaluate. Try again on the next poll.
    }
    await Bun.sleep(pollMs);
  }

  console.warn(`No verdict for ${url} (last page title: "${lastTitle}")`);
  return "unknown";
}

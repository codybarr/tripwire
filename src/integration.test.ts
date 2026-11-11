import { afterAll, expect, test } from "bun:test";
import { observe } from "./browser";
import { schemaOrgOffer } from "./detectors";
import { createNtfy } from "./ntfy";

const received: { body: unknown; auth: string | null }[] = [];

const server = Bun.serve({
  port: 0,
  async fetch(request) {
    const { pathname } = new URL(request.url);
    if (request.method === "POST") {
      received.push({ body: await request.json(), auth: request.headers.get("authorization") });
      return new Response(pathname === "/" ? "{}" : "nope", { status: pathname === "/" ? 200 : 500 });
    }
    const availability = pathname === "/in" ? "InStock" : "OutOfStock";
    const ld = JSON.stringify({ "@type": "Product", offers: { availability: `https://schema.org/${availability}` } });
    return new Response(`<script type="application/ld+json">${ld}</script><p>page</p>`, {
      headers: { "Content-Type": "text/html" },
    });
  },
});

afterAll(() => server.stop(true));

test("reads availability from a real browser", async () => {
  expect(await observe(`${server.url}in`, schemaOrgOffer)).toBe("available");
  expect(await observe(`${server.url}out`, schemaOrgOffer)).toBe("unavailable");
}, 60_000);

test("gives up with unknown when the page has no data", async () => {
  const never = () => "unknown" as const;
  expect(await observe(`${server.url}in`, never, { timeoutMs: 500, pollMs: 100 })).toBe("unknown");
}, 60_000);

test("publishes to ntfy", async () => {
  const notify = createNtfy({ topic: "t", server: server.url.origin, token: "secret" });
  await notify({ title: "T", message: "M", click: "https://shop.test" });
  expect(received.at(-1)).toEqual({
    body: { topic: "t", priority: 4, tags: ["tada"], title: "T", message: "M", click: "https://shop.test" },
    auth: "Bearer secret",
  });
});

test("throws when ntfy rejects the message", async () => {
  const notify = createNtfy({ topic: "t", server: `${server.url.origin}/fail` });
  await expect(notify({ title: "T", message: "M", click: "x" })).rejects.toThrow("500");
});

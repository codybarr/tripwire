export type Availability = "available" | "unavailable" | "unknown";

export type PageSnapshot = {
  url: string;
  title: string;
  text: string;
  jsonLd: string[];
};

export type Detector = (page: PageSnapshot, targetUrl: string) => Availability;

const AVAILABLE = new Set(["InStock", "LimitedAvailability", "OnlineOnly", "PreOrder", "PreSale", "BackOrder"]);
const UNAVAILABLE = new Set(["OutOfStock", "SoldOut", "Discontinued", "InStoreOnly"]);

type Offer = { url?: unknown; availability?: unknown };

function parse(block: string): unknown {
  try {
    return JSON.parse(block);
  } catch {
    return undefined;
  }
}

function collectOffers(node: unknown, offers: Offer[]): void {
  if (Array.isArray(node)) {
    for (const item of node) collectOffers(item, offers);
    return;
  }
  if (typeof node !== "object" || node === null) return;

  const record = node as Record<string, unknown>;
  if ("availability" in record) offers.push(record);
  collectOffers(record.offers, offers);
  collectOffers(record.hasVariant, offers);
  collectOffers(record["@graph"], offers);
}

function classify(offer: Offer): Availability {
  if (typeof offer.availability !== "string") return "unknown";
  const name = offer.availability.split("/").pop() ?? "";
  if (AVAILABLE.has(name)) return "available";
  if (UNAVAILABLE.has(name)) return "unavailable";
  return "unknown";
}

/**
 * Reads schema.org Product data, which most stores publish for search engines.
 * On a multi-variant page the offer must match the target URL exactly, so one
 * variant's stock is never mistaken for another's.
 */
export const schemaOrgOffer: Detector = (page, targetUrl) => {
  const offers: Offer[] = [];
  for (const block of page.jsonLd) collectOffers(parse(block), offers);

  const match = offers.find((offer) => offer.url === targetUrl);
  if (match) return classify(match);
  return offers.length === 1 ? classify(offers[0]!) : "unknown";
};

/** For pages without structured data. Checks `unavailable` first. */
export function textMatch(patterns: { available: RegExp; unavailable: RegExp }): Detector {
  return (page) => {
    if (patterns.unavailable.test(page.text)) return "unavailable";
    if (patterns.available.test(page.text)) return "available";
    return "unknown";
  };
}

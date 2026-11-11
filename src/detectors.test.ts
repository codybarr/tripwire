import { describe, expect, test } from "bun:test";
import { schemaOrgOffer, textMatch, type PageSnapshot } from "./detectors";

const target = "https://shop.test/p?variant=2";
const page = (jsonLd: unknown[], text = ""): PageSnapshot => ({
  url: target,
  title: "",
  text,
  jsonLd: jsonLd.map((block) => JSON.stringify(block)),
});
const offer = (url: string, availability: string) => ({ url, availability: `https://schema.org/${availability}` });

describe("schemaOrgOffer", () => {
  test("reads the target variant, not its siblings", () => {
    const group = {
      "@type": "ProductGroup",
      hasVariant: [
        { offers: offer("https://shop.test/p?variant=1", "InStock") },
        { offers: offer(target, "OutOfStock") },
      ],
    };
    expect(schemaOrgOffer(page([group]), target)).toBe("unavailable");
  });

  test("uses the only offer on a single-product page", () => {
    const product = { "@type": "Product", offers: offer("https://shop.test/p", "InStock") };
    expect(schemaOrgOffer(page([product]), target)).toBe("available");
  });

  test("is unknown when several offers exist and none match", () => {
    const product = {
      offers: [offer("https://shop.test/a", "InStock"), offer("https://shop.test/b", "InStock")],
    };
    expect(schemaOrgOffer(page([product]), target)).toBe("unknown");
  });

  test("is unknown on a page with no usable data", () => {
    expect(schemaOrgOffer({ ...page([]), jsonLd: ["{not json"] }, target)).toBe("unknown");
  });
});

describe("textMatch", () => {
  const detect = textMatch({ available: /add to cart/i, unavailable: /sold out/i });

  test("prefers unavailable when both match", () => {
    expect(detect(page([], "Add to cart Sold out"), target)).toBe("unavailable");
  });

  test("detects available", () => {
    expect(detect(page([], "ADD TO CART"), target)).toBe("available");
  });

  test("is unknown when neither matches", () => {
    expect(detect(page([], "Checking your browser"), target)).toBe("unknown");
  });
});

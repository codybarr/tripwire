import { schemaOrgOffer } from "./src/detectors";
import type { Check } from "./src/run";

// Add an entry here to watch another page.
export const checks: Check[] = [
  {
    id: "nuphy-halo75-v2-obsidian-mint",
    title: "NuPhy Halo75 V2 (Obsidian Black, Mint)",
    url: "https://nuphy.com/products/halo75-v2-qmk-via-wireless-custom-mechanical-keyboard?variant=41037253804141",
    detect: schemaOrgOffer,
  },
];

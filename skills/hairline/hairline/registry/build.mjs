#!/usr/bin/env node
/**
 * Writes the shadcn registry item into the site's public folder.
 *
 * `shadcn add` fetches an item by absolute URL, so a hostname has to be in the
 * output and may not be in the source: it comes from the environment (see
 * scripts/base-url.mjs). Everything under apps/site/public/r is generated.
 */
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { FALLBACK, resolveBase } from "../scripts/base-url.mjs";

const SRC = join(import.meta.dirname, "src");
const OUT = join(import.meta.dirname, "..", "apps", "site", "public", "r");

const resolved = resolveBase();
if (resolved.source === "fallback") {
  console.warn(`[registry] no site URL in the environment; using ${FALLBACK}.\n[registry] A deployed build that prints this line has published an item that points at localhost.`);
}
const BASE = resolved.url.replace(/\/+$/, "");

const item = {
  $schema: "https://ui.shadcn.com/schema/registry-item.json",
  name: "hairline",
  type: "registry:ui",
  title: "Hairline",
  description: "Six isometric line figures that answer the pointer, with their palette mapped to your theme's tokens.",
  dependencies: ["@lucasmarkes/hairline"],
  files: [{ path: "components/ui/hairline.tsx", type: "registry:ui", content: readFileSync(join(SRC, "hairline.tsx"), "utf8") }],
  docs: `Docs: ${BASE}`,
};

rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });
writeFileSync(join(OUT, "hairline.json"), JSON.stringify(item, null, 2) + "\n");
writeFileSync(join(OUT, "registry.json"), JSON.stringify({ $schema: "https://ui.shadcn.com/schema/registry.json", name: "hairline", homepage: BASE, items: [item] }, null, 2) + "\n");

console.log(`[registry] ${BASE}/r/hairline.json (base from ${resolved.source})`);

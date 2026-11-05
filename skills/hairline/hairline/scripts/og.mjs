#!/usr/bin/env node
/**
 * Photographs the site's /og route into apps/site/public/og.png, the Open
 * Graph card. The result is committed; run this again when the figures or the
 * card change.
 *
 *   pnpm build && pnpm --filter @hairline/site start     (in one terminal)
 *   node scripts/og.mjs [http://localhost:3000]          (in another)
 */
import { createRequire } from "node:module";
import { join, resolve } from "node:path";

const ROOT = resolve(import.meta.dirname, "..");
const SITE = join(ROOT, "apps/site");
const { chromium } = createRequire(join(SITE, "package.json"))("@playwright/test");
const base = (process.argv[2] ?? "http://localhost:3000").replace(/\/+$/, "");

const browser = await chromium.launch({ channel: "chrome" });
const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 2 });
try {
  await page.goto(`${base}/og`, { waitUntil: "networkidle" });
} catch {
  console.error(`Nothing at ${base}/og. Build and start the site first:\n  pnpm build && pnpm --filter @hairline/site start`);
  await browser.close();
  process.exit(1);
}
await page.waitForFunction(() => document.querySelectorAll("[data-hairline] > svg > *").length >= 1 && document.fonts.status === "loaded");
// let the figure finish its first frames, then sweep the pointer across it so its layers stand open, and let them settle
await page.waitForTimeout(1200);
for (let x = 560; x <= 1160; x += 24) await page.mouse.move(x, 300, { steps: 2 });
await page.waitForTimeout(1500);
const out = join(SITE, "public/og.png");
await page.screenshot({ path: out, clip: { x: 0, y: 0, width: 1200, height: 630 } });
await browser.close();
console.log(`wrote ${out}`);

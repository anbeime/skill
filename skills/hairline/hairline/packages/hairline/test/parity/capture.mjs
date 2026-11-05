/**
 * Captures the goldens: what the six figures draw on lucasmarkes.com/lab/hairline,
 * checkpoint by checkpoint, under the scripts in scripts.mjs. The package's
 * parity test (test/browser/parity.spec.ts) must draw the same.
 *
 *   node test/parity/capture.mjs <commit> [url]
 *
 * <commit> is the website commit being served, recorded in each golden.
 * [url] is where a production build of it is running (default http://localhost:3124).
 * Every figure is captured twice, and a difference between the two is an error.
 */
import { chromium } from "@playwright/test";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { play } from "./driver.mjs";
import { FIGURES, OPTION, SCRIPTS } from "./scripts.mjs";

const [commit, base = "http://localhost:3124"] = process.argv.slice(2);
if (!commit) { console.error("usage: node test/parity/capture.mjs <commit> [url]"); process.exit(1); }

const here = (p) => new URL(p, import.meta.url);
const clock = readFileSync(here("./clock.js"), "utf8") + "\nwindow.__freeze(1000);";
const VIEWPORT = { width: 1200, height: 900 };

async function capture(browser, id) {
  const context = await browser.newContext({ viewport: VIEWPORT, deviceScaleFactor: 1, colorScheme: "light", reducedMotion: "no-preference" });
  await context.addInitScript(clock);
  const page = await context.newPage();
  await page.goto(`${base}/lab/hairline`);
  if (await page.locator("nextjs-portal").count()) throw new Error("This is the dev server. Capture against a production build (pnpm build && pnpm start).");
  const figure = page.locator("figure.hairline").nth(FIGURES.indexOf(id)), stage = figure.locator(".hl-stage");
  await stage.locator("svg.fg > *").first().waitFor();
  await stage.evaluate((el) => {
    const r = el.getBoundingClientRect();
    window.scrollTo({ top: window.scrollY + r.top + r.height / 2 - innerHeight / 2, behavior: "instant" });
  });
  await page.evaluate(() => new Promise((done) => window.__realTimeout(done, 500)));
  const input = figure.locator("input[type=range]"), value = OPTION[id][1];
  const checkpoints = await play(page, {
    stage,
    snap: () => stage.evaluate((el) => ({ svg: el.querySelector("svg").innerHTML, read: el.querySelector(".hl-read").textContent })),
    /* the slider is React's: set it the way a user's drag would, then give React real time to render */
    set: async () => {
      await input.evaluate((el, v) => {
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(el, String(v));
        el.dispatchEvent(new Event("input", { bubbles: true }));
      }, value);
      await page.waitForFunction(([el, v]) => Number(el.value) === v, [await input.elementHandle(), value]);
      await page.evaluate(() => new Promise((done) => window.__realTimeout(done, 150)));
    },
  }, SCRIPTS[id]);
  await context.close();
  return checkpoints;
}

const browser = await chromium.launch({ channel: "chrome", headless: true });
mkdirSync(here("./golden/"), { recursive: true });
let failed = false;
for (const id of FIGURES) {
  const first = await capture(browser, id), second = await capture(browser, id);
  if (JSON.stringify(first) !== JSON.stringify(second)) { console.error(`✗ ${id}: two captures differ; the golden would not be reproducible`); failed = true; continue; }
  const golden = { source: { site: "lucasmarkes.com/lab/hairline", commit }, viewport: VIEWPORT, option: OPTION[id], checkpoints: first };
  writeFileSync(here(`./golden/${id}.json`), JSON.stringify(golden, null, 1) + "\n");
  console.log(`✓ ${id}: ${first.map((c) => `${c.at} "${c.read}"`).join(" · ")}`);
}
await browser.close();
process.exit(failed ? 1 : 0);

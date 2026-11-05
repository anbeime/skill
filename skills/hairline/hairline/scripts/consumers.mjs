#!/usr/bin/env node
/**
 * Layer 6: the package as a stranger gets it. Packs it, installs the tarball
 * with npm into a copy of each fixture (outside the workspace, so nothing
 * resolves through a symlink), builds the fixture with its own toolchain,
 * serves the build and opens it in Chrome.
 *
 *   node scripts/consumers.mjs          both fixtures
 *   node scripts/consumers.mjs next     one of them (next | vite)
 *
 * Needs the network (npm installs next, react and vite) and a built package.
 */
import { execFileSync, spawn } from "node:child_process";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const ROOT = resolve(import.meta.dirname, "..");
const PKG = join(ROOT, "packages/hairline");
const { chromium } = createRequire(join(PKG, "package.json"))("@playwright/test");

const FIXTURES = {
  next: { dir: "fixtures/next-app", port: 4311, serve: (port) => ["npx", ["next", "start", "-p", String(port)]], figures: ["riffle", "slow", "phosphor"] },
  vite: { dir: "fixtures/vite-vanilla", port: 4312, serve: (port) => ["npx", ["vite", "preview", "--port", String(port), "--strictPort"]], figures: ["riffle", "terrain", "exploded", "phosphor", "slow", "turntable", "keyboard", "elevator", "phone", "laptop", "terminal", "cabinet", "branches", "vault", "lockers", "padlock", "patch", "dish", "router", "loupe", "sieve", "rail", "plug", "query", "drawer", "basket", "plot", "hub", "relay", "settle", "format", "rebuild", "stack"] },
};
const only = process.argv[2];
if (only && !FIXTURES[only]) { console.error(`Unknown fixture "${only}". Use: ${Object.keys(FIXTURES).join(" | ")}`); process.exit(2); }

let failures = 0;
const fail = (msg) => { failures++; console.error(`  ✗ ${msg}`); };
const pass = (msg) => console.log(`  ✓ ${msg}`);
const check = (ok, good, bad) => (ok ? pass(good) : fail(bad));
const run = (cmd, args, cwd) => execFileSync(cmd, args, { cwd, encoding: "utf8", stdio: "pipe" });
function step(label, cmd, args, cwd) {
  try { run(cmd, args, cwd); pass(label); return true; }
  catch (err) { fail(`${label}\n${String((err.stdout ?? "") + (err.stderr ?? "") || err.message).trim().split("\n").slice(-30).join("\n")}`); return false; }
}
async function up(url, tries = 100) {
  for (let i = 0; i < tries; i++) {
    try { if ((await fetch(url)).ok) return true; } catch {}
    await new Promise((r) => setTimeout(r, 200));
  }
  return false;
}

/**
 * Counts the animation frames requested between one frame and the next. A
 * page with any number of figures keeps one loop, so it asks for one frame per
 * frame; a second copy of the engine would ask for two.
 */
const COUNT_FRAMES = `(() => {
  const raf = window.requestAnimationFrame.bind(window);
  let asked = 0;
  window.__asked = [];
  window.requestAnimationFrame = (fn) => { asked++; return raf(fn); };
  const tally = () => { window.__asked.push(asked); asked = 0; raf(tally); };
  raf(tally);
})();`;

const staging = mkdtempSync(join(tmpdir(), "hairline-consumers-"));
console.log("\n▸ tarball");
step("pnpm pack", "pnpm", ["pack", "--pack-destination", staging], PKG);
const tgz = readdirSync(staging).filter((f) => f.endsWith(".tgz")).map((f) => join(staging, f))[0];
if (!tgz) { console.error("\nNo tarball to install.\n"); process.exit(1); }

const browser = await chromium.launch({ channel: "chrome" });
for (const [name, fx] of Object.entries(FIXTURES)) {
  if (only && only !== name) continue;
  console.log(`\n▸ ${fx.dir}`);
  const dir = join(staging, name);
  cpSync(join(ROOT, fx.dir), dir, { recursive: true, filter: (src) => !/\/(node_modules|\.next|dist)$/.test(src) });
  if (name === "next") {
    // what `shadcn add` does with the registry item: write its file into the app
    run("node", ["registry/build.mjs"], ROOT);
    const item = JSON.parse(readFileSync(join(ROOT, "apps/site/public/r/hairline.json"), "utf8"));
    for (const file of item.files) {
      mkdirSync(join(dir, file.path, ".."), { recursive: true });
      writeFileSync(join(dir, file.path), file.content);
    }
    pass("the registry item's file is in place");
  }
  if (!step("npm install (the tarball, as a dependency)", "npm", ["install", "--no-audit", "--no-fund", tgz], dir)) continue;
  if (!step("build (the fixture's own typecheck and bundler)", "npm", ["run", "build"], dir)) continue;

  const [cmd, args] = fx.serve(fx.port);
  const server = spawn(cmd, args, { cwd: dir, stdio: "ignore" });
  try {
    const url = `http://localhost:${fx.port}/`;
    if (!(await up(url))) { fail(`nothing answered at ${url}`); continue; }

    if (name === "next") {
      const html = await (await fetch(url)).text();
      check(/<div id="riffle"[^>]*><\/div>/.test(html), "the server renders an empty <div> for a figure", "the server-rendered page has no empty <div id=\"riffle\">");
      check(!html.includes("<svg"), "no figure is drawn on the server", "the server-rendered page already has an <svg>");
    }

    const context = await browser.newContext({ viewport: { width: 1200, height: 900 } });
    await context.addInitScript(COUNT_FRAMES);
    const page = await context.newPage();
    const noise = [];
    page.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") noise.push(`${m.type()}: ${m.text()}`); });
    page.on("pageerror", (e) => noise.push(`pageerror: ${e}`));
    await page.goto(url, { waitUntil: "networkidle" });

    for (const id of fx.figures) {
      const drawn = await page.locator(`#${id} svg > *`).first().waitFor({ timeout: 5000 }).then(() => true, () => false);
      const box = drawn ? await page.locator(`#${id} svg`).boundingBox() : null;
      check(drawn && box.width > 100 && Math.abs(box.width / box.height - 1.25) < 0.01, `${id} is drawn, 5:4`, `${id} is not drawn (box ${JSON.stringify(box)})`);
    }
    check((await page.locator("style[data-hairline-style]").count()) === 0 && (await page.evaluate(() => document.adoptedStyleSheets.length)) === 1,
      "one adopted stylesheet for every figure", "the figures did not share one adopted stylesheet");

    await page.waitForTimeout(500);
    const asked = await page.evaluate(() => { const from = window.__asked.length; return new Promise((r) => setTimeout(() => r(window.__asked.slice(from)), 500)); });
    check(asked.length > 10 && asked.every((n) => n === 1), `one loop for ${fx.figures.length} figures (${asked.length} frames, one request each)`, `expected one frame request per frame, saw ${[...new Set(asked)].join(", ")} over ${asked.length} frames`);

    if (name === "next") {
      await page.goto(`${url}registry`, { waitUntil: "networkidle" });
      const fill = await page.locator("#themed svg path").first().evaluate((el) => getComputedStyle(el).fill).catch(() => "");
      check(fill === "rgb(16, 16, 20)", "the registry item draws with the app's tokens", `the registry item's figure is filled ${fill || "(not drawn)"}, not --background`);
    }
    if (name === "vite") check((await page.locator("#read").textContent()) !== "", "onRead reached the page", "onRead never wrote to the page");
    check(noise.length === 0, "console is clean", `console:\n${noise.join("\n")}`);
    await context.close();
  } finally {
    server.kill();
  }
}
await browser.close();
rmSync(staging, { recursive: true, force: true });

if (failures) { console.error(`\n${failures} consumer check${failures > 1 ? "s" : ""} failed.\n`); process.exit(1); }
console.log("\nBoth consumers install, build and draw.\n");

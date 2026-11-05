import { expect, test } from "@playwright/test";
import { execFile } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, symlinkSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { inflateSync } from "node:zlib";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * The skill's read.mjs, run as an agent runs it: from a working directory, on
 * a fixture, with the look's cache holding this repo's playwright-core, so
 * nothing is installed and it drives the same Chrome.
 */
const SKILL = fileURLToPath(new URL("../../../../skills/hairline-create/", import.meta.url));
const FIX = fileURLToPath(new URL("../skill/fixtures/", import.meta.url));
const from = (pkg: string, at: string) => createRequire(at).resolve(pkg + "/package.json");
const CORE = dirname(from("playwright-core", from("playwright", from("@playwright/test", import.meta.url))));

const cache = mkdtempSync(join(tmpdir(), "hl-read-cache-"));
mkdirSync(join(cache, "node_modules"));
symlinkSync(CORE, join(cache, "node_modules", "playwright-core"), "dir");

type Run = { code: number; out: string };
/** read.mjs with these arguments; node is named by its path, so a test can empty the PATH. */
function read(cwd: string, env: Record<string, string>, ...args: string[]): Promise<Run> {
  return new Promise((done) => {
    execFile(process.execPath, [SKILL + "read.mjs", ...args], { cwd, env: { ...process.env, ...env }, timeout: 50_000 }, (err, stdout, stderr) => {
      done({ code: err ? (typeof err.code === "number" ? err.code : -1) : 0, out: stdout + stderr });
    });
  });
}
const PNG = "89504e470d0a1a0a";
/** The top-left pixel of a PNG: the first pixel of the first row is stored as is, whatever the row's filter. */
function corner(png: Buffer): number[] {
  const data: Buffer[] = [];
  for (let at = 8; at < png.length;) {
    const size = png.readUInt32BE(at), type = png.toString("ascii", at + 4, at + 8);
    if (type === "IDAT") data.push(png.subarray(at + 8, at + 8 + size));
    at += 12 + size;
  }
  return [...inflateSync(Buffer.concat(data)).subarray(1, 4)];
}

test.describe("read.mjs", () => {
  test.setTimeout(60_000);

  test("writes the picture and the full card for an icon, and prints the card", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-read-"));
    const run = await read(cwd, { HAIRLINE_LOOK_CACHE: cache }, FIX + "rocket.svg");
    expect(run.code, run.out).toBe(0);
    const png = join(cwd, "hairline-rocket-source.png"), txt = join(cwd, "hairline-rocket-source.txt");
    const bytes = readFileSync(png);
    expect(bytes.subarray(0, 8).toString("hex")).toBe(PNG);
    /* 400 × 400 CSS pixels, taken at twice the density */
    expect([bytes.readUInt32BE(16), bytes.readUInt32BE(20)]).toEqual([800, 800]);
    const card = readFileSync(txt, "utf8");
    expect(run.out).toContain(card.trimEnd());
    expect(card.split("\n")[0]).toBe("rocket.svg  viewBox 0 0 24 24  (1:1)  5 shapes in 2 groups");
    expect(card).toContain('title: "Deploy"   ids: rocket, body, window, fin-left, fin-right, flame');
    /* getBBox is geometry: the body's box is the path's, 8..16 × 2..17 */
    expect(card).toMatch(/^#1 {2}path {4}g#rocket {2}box 8\.\.16 × 2\.\.17 {2}centre 12,9\.5 {2}stroke 1\.5 {2}closed, curves and lines/m);
    expect(card).toMatch(/^#2 {2}circle {2}g#rocket {2}box 10\.5\.\.13\.5 × 7\.\.10 .* filled {2}closed, curves {2}inside #1, middle$/m);
    expect(card).toMatch(/^#4 {2}path {4}g#rocket .* mirror of #3$/m);
    expect(card).toMatch(/^#5 {2}path {4}g#flame .* filled {2}closed, curves {2}below #1, touching$/m);
    expect(run.out).toMatch(/^picture .*hairline-rocket-source\.png$/m);
    expect(run.out).toMatch(/^card .*hairline-rocket-source\.txt$/m);
  });

  test("measures a file with width and height and no viewBox, and leaves <defs> out", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-read-"));
    const run = await read(cwd, { HAIRLINE_LOOK_CACHE: cache }, FIX + "mixed.svg", "--name", "Mixed One");
    expect(run.code, run.out).toBe(0);
    const card = readFileSync(join(cwd, "hairline-mixed-one-source.txt"), "utf8");
    expect(card.split("\n")[0]).toBe("mixed.svg  viewBox 0 0 48 32 (from width and height)  (1.5:1)  2 shapes in 0 groups");
    /* the rect, and the circle the <use> brings in at 8,8; nothing from <defs> itself */
    expect(card).toMatch(/^#1 {2}rect /m);
    expect(card).toMatch(/^#2 {2}use {5}- {9}box 8\.\.12 × 8\.\.12 /m);
    expect(card).not.toMatch(/^#3 /m);
    expect(card).toContain("not read: 1 <use> outside the file, 1 <text>, 1 <image>");
  });

  test("puts a transformed shape where it is drawn, not where its own coordinates say", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-read-"));
    const run = await read(cwd, { HAIRLINE_LOOK_CACHE: cache }, FIX + "moved.svg");
    expect(run.code, run.out).toBe(0);
    expect(readFileSync(join(cwd, "hairline-moved-source.txt"), "utf8")).toMatch(/^#1 {2}rect {4}g#moved {3}box 20\.\.30 × 40\.\.50 /m);
  });

  test("measures a shape inside a nested <svg> where it is drawn", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-read-"));
    const run = await read(cwd, { HAIRLINE_LOOK_CACHE: cache }, FIX + "nested.svg");
    expect(run.code, run.out).toBe(0);
    expect(readFileSync(join(cwd, "hairline-nested-source.txt"), "utf8")).toMatch(/^#2 {2}rect {4}- {9}box 0\.\.12 × 0\.\.12 /m);
  });

  test("never runs the SVG's scripts: the card is of the drawing as written", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-read-"));
    const run = await read(cwd, { HAIRLINE_LOOK_CACHE: cache }, FIX + "scripted.svg");
    expect(run.code, run.out).toBe(0);
    expect(readFileSync(join(cwd, "hairline-scripted-source.txt"), "utf8")).toMatch(/^#1 {2}rect {4}- {9}box 10\.\.90 × 10\.\.90 /m);
  });

  test("draws light ink on dark, and says so on the ink line", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-read-"));
    const run = await read(cwd, { HAIRLINE_LOOK_CACHE: cache }, FIX + "light.svg");
    expect(run.code, run.out).toBe(0);
    const card = readFileSync(join(cwd, "hairline-light-source.txt"), "utf8");
    expect(card.split("\n")[2]).toBe("ink: 4..20 × 4..20  (67% × 67% of the viewBox)  light ink: the picture is on dark");
    expect(corner(readFileSync(join(cwd, "hairline-light-source.png")))).toEqual([24, 24, 27]);
    /* dark ink stays on white */
    await read(cwd, { HAIRLINE_LOOK_CACHE: cache }, FIX + "rocket.svg");
    expect(corner(readFileSync(join(cwd, "hairline-rocket-source.png")))).toEqual([255, 255, 255]);
  });

  test("lists each piece of a path drawn in several, a relative move after a close included", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-read-"));
    const run = await read(cwd, { HAIRLINE_LOOK_CACHE: cache }, FIX + "compound.svg");
    expect(run.code, run.out).toBe(0);
    const card = readFileSync(join(cwd, "hairline-compound-source.txt"), "utf8");
    expect(card.split("\n")[0]).toBe("compound.svg  viewBox 0 0 20 20  (1:1)  3 shapes in 0 groups");
    expect(card).toMatch(/^#1 {2}path {4}- {9}box 2\.\.8 × 2\.\.8 .* closed, lines, part 1 of 3/m);
    /* m10 0 after z starts at the first piece's start, 2,2, so at 12,2 */
    expect(card).toMatch(/^#2 {2}path {4}- {9}box 12\.\.18 × 2\.\.8 .* closed, lines, part 2 of 3/m);
    expect(card).toMatch(/^#3 {2}path {4}- {9}box 2\.\.18 × 12\.\.18 .* closed, curves and lines, part 3 of 3/m);
  });

  test("without a browser, writes the reduced card, no picture, and exits 0", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-read-"));
    /* an empty cache, no npm on the PATH and no NODE_PATH (pnpm sets one): playwright-core cannot be had */
    const empty = mkdtempSync(join(tmpdir(), "hl-read-nocache-"));
    const run = await read(cwd, { HAIRLINE_LOOK_CACHE: empty, PATH: "", NODE_PATH: "" }, FIX + "rocket.svg");
    expect(run.code, run.out).toBe(0);
    expect(existsSync(join(cwd, "hairline-rocket-source.png"))).toBe(false);
    const card = readFileSync(join(cwd, "hairline-rocket-source.txt"), "utf8");
    expect(card).toContain("shapes: 4 path, 1 circle");
    expect(card).toContain("no browser: boxes and the picture were not taken");
    expect(run.out).toMatch(/^no browser: /m);
  });

  test("refuses what it cannot read, with one line and exit 2", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-read-"));
    const bad = await read(cwd, { HAIRLINE_LOOK_CACHE: cache }, FIX + "broken.txt");
    expect(bad.code).toBe(2);
    expect(bad.out.trim()).toBe("read: broken.txt is not an SVG: no <svg> root");
    const none = await read(cwd, { HAIRLINE_LOOK_CACHE: cache }, join(cwd, "missing.svg"));
    expect(none.code).toBe(2);
    expect(none.out).toMatch(/^read: cannot read .*missing\.svg$/m);
    const usage = await read(cwd, { HAIRLINE_LOOK_CACHE: cache });
    expect(usage.code).toBe(2);
    expect(usage.out).toMatch(/^usage: node read\.mjs <file\.svg> \[--name <name>\]$/m);
  });
});

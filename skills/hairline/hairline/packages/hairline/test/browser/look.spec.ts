import { expect, test } from "@playwright/test";
import { execFile } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, symlinkSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

/**
 * The skill's look.mjs, run as an agent runs it: from a working directory, on
 * the examples, on figures that give their own points, and on a figure that
 * throws. Its cache is a folder holding this repo's playwright-core, so nothing
 * is installed, and it drives the same Chrome.
 */
const SKILL = fileURLToPath(new URL("../../../../skills/hairline-create/", import.meta.url));
const from = (pkg: string, at: string) => createRequire(at).resolve(pkg + "/package.json");
const CORE = dirname(from("playwright-core", from("playwright", from("@playwright/test", import.meta.url))));

const cache = mkdtempSync(join(tmpdir(), "hl-look-cache-"));
mkdirSync(join(cache, "node_modules"));
symlinkSync(CORE, join(cache, "node_modules", "playwright-core"), "dir");

type Run = { code: number; out: string };
/** look.mjs with these arguments, in a fresh working directory. */
function look(cwd: string, ...args: string[]): Promise<Run> {
  return new Promise((done) => {
    execFile("node", [SKILL + "look.mjs", ...args], { cwd, env: { ...process.env, HAIRLINE_LOOK_CACHE: cache }, timeout: 50_000 }, (err, stdout, stderr) => {
      done({ code: err ? (typeof err.code === "number" ? err.code : -1) : 0, out: stdout + stderr });
    });
  });
}
const PNG = "89504e470d0a1a0a";
/** Whether look.mjs wrote this picture in the working directory, as a PNG. */
function wrote(cwd: string, png: string) {
  expect(existsSync(join(cwd, png)), png).toBe(true);
  expect(readFileSync(join(cwd, png)).subarray(0, 8).toString("hex"), png).toBe(PNG);
}
/* The examples give no points of their own, so a figure that does is Terrain with these keys added to its hairline({ … }) call. */
function declaring(keys: string) {
  const src = readFileSync(SKILL + "examples/terrain.js", "utf8").replace("  range: [1.5, 3, 5],\n", `  range: [1.5, 3, 5],\n${keys}`);
  expect(src).toContain(keys);
  return src;
}

test.describe("look.mjs", () => {
  test.setTimeout(60_000);

  test("--source puts the SVG beside rest on the sheet, and says so", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-look-"));
    const svg = fileURLToPath(new URL("../skill/fixtures/rocket.svg", import.meta.url));
    const run = await look(cwd, `${SKILL}examples/terrain.js`, "--answer", "30,90,0", "--source", svg);
    expect(run.code, run.out).toBe(0);
    expect(run.out).toMatch(/^source .*rocket\.svg is on the sheet beside rest: look\.md, item 14\.$/m);
    wrote(cwd, "hairline-terrain-look.png");
    /* one more row: Terrain's sheet is 1786 pixels tall without a source, about 2500 with one */
    expect(readFileSync(join(cwd, "hairline-terrain-look.png")).readUInt32BE(20)).toBeGreaterThan(2200);
  });

  test("--source that cannot be read stops before the browser, with exit 2", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-look-"));
    const run = await look(cwd, `${SKILL}examples/terrain.js`, "--source", join(cwd, "missing.svg"));
    expect(run.code).toBe(2);
    expect(run.out).toMatch(/^look: cannot read the source .*missing\.svg$/m);
    expect(existsSync(join(cwd, "hairline-terrain.html"))).toBe(false);
  });

  for (const [name, answer, read] of [["terrain", "30,90,0", "cell 2·6"], ["riffle", "42,28,52", "05"]]) {
    test(`passes ${name}, writes its sheet and prints the read-outs`, async () => {
      const cwd = mkdtempSync(join(tmpdir(), "hl-look-"));
      const run = await look(cwd, `${SKILL}examples/${name}.js`, "--answer", answer, "--zoom", "answer");
      expect(run.code, run.out).toBe(0);
      expect(run.out).toMatch(new RegExp(`^answer ${answer} -> at=\\d+,\\d+$`, "m"));
      expect(run.out).toMatch(/^9 frame: ok\. /m);
      expect(run.out).toMatch(/^8 read-out: ok\. rest "rest", answer "/m);
      expect(run.out).toContain(`answer "${read}"`);
      expect(run.out).toMatch(/^12 console: ok\. /m);
      /* both examples' answers move well over the line: Terrain's 74% of the thumbnail's ink, Riffle's 139% */
      expect(run.out).toMatch(/^3 answer: ok\. At 240px the pointer moves \d+% of the ink, .* over those drawn at rest\.$/m);
      /* 4 is information: a busy machine can say moving, so only its shape is held */
      expect(run.out).toMatch(/^4 flicker: (still|moving)\. .* Information, not a check: look\.md, item 4\.$/m);
      expect(run.out).toMatch(new RegExp(`^blind .*hairline-${name}-blind\\.png holds the small and small-answer pictures with the name and the read-out hidden`, "m"));
      expect(run.out).toMatch(new RegExp(`^motion .*hairline-${name}-motion\\.png is the stage while the answer plays: 16 pictures, rest first`, "m"));
      for (const png of ["look", "answer", "blind", "motion"]) wrote(cwd, `hairline-${name}-${png}.png`);
    });
  }

  test("takes the answer and the edges from the figure when the command gives none", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-look-"));
    writeFileSync(join(cwd, "terrain.js"), declaring("  answer: [30, 90, 0],\n  edge: [[6, 6, 0], [120, 120, 0]],\n"));
    const run = await look(cwd, "terrain.js");
    expect(run.code, run.out).toBe(0);
    expect(run.out).toMatch(/^answer 30,90,0 \(from the figure's hairline call\) -> at=\d+,\d+ · edge 6,6,0 \(from the figure's hairline call\) -> at=\d+,\d+ · edge 120,120,0 \(from the figure's hairline call\) -> at=\d+,\d+$/m);
    expect(run.out).toContain('answer "cell 2·6"');
    /* the slider's two ends are taken at the two edges, the first for intensity 0 */
    expect(run.out).toContain('low "cell 0·0", high "cell 8·8"');
    expect(run.out).not.toContain("no --answer");
    expect(run.out).not.toContain("no --edge");
    expect(run.out).toMatch(/^3 answer: ok\. /m);
    expect(run.out).toMatch(/^motion .*hairline-terrain-motion\.png /m);
    wrote(cwd, "hairline-terrain-motion.png");
  });

  test("a point on the command line wins over the figure's", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-look-"));
    writeFileSync(join(cwd, "terrain.js"), declaring("  answer: [30, 90, 0],\n  edge: [[6, 6, 0], [120, 120, 0]],\n"));
    const run = await look(cwd, "terrain.js", "--answer", "100,30,0");
    expect(run.code, run.out).toBe(0);
    /* --answer wins; the edges, not given on the command line, are still the figure's */
    expect(run.out).toMatch(/^answer 100,30,0 -> at=\d+,\d+ · edge 6,6,0 \(from the figure's hairline call\) -> /m);
    expect(run.out).toContain('answer "cell 7·2"');
    expect(run.out).not.toContain("cell 2·6");
  });

  test("says so when the figure's points are not points, and looks on at rest", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-look-"));
    writeFileSync(join(cwd, "terrain.js"), declaring('  answer: ["a", 1],\n  edge: [[1, 2, 3], [4, 5, 6], [7, 8, 9]],\n'));
    const run = await look(cwd, "terrain.js");
    expect(run.out).toMatch(/^the figure's hairline call gives answer a,1, which is not a point: two numbers for the viewBox, three for the world\. Give --answer x,y,z instead\.$/m);
    expect(run.out).toMatch(/^the figure's hairline call gives edge \[\[1,2,3\],\[4,5,6\],\[7,8,9\]\], which is not one point or two\. Give --edge x,y,z instead\.$/m);
    expect(run.out).toMatch(/^no --answer: /m);
    expect(run.out).toMatch(/^3 answer: not measured\. /m);
    expect(run.code, run.out).toBe(0);
  });

  test("warns, and does not fail, when the answer only lights a stroke", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-look-"));
    const src = readFileSync(SKILL + "examples/terrain.js", "utf8")
      .replace("c.sp.t = HMAX * falloff(Math.hypot(dx, dy) / R);", "c.sp.t = c.h0;")
      .replace('want = byCell.get(i + "," + j);', 'byCell.get(i + "," + j).el.sil.classList.add("hi");');
    expect(src).toContain('classList.add("hi")');
    writeFileSync(join(cwd, "terrain.js"), src);
    const run = await look(cwd, "terrain.js", "--answer", "30,90,0");
    /* a change of colour moves next to no ink */
    expect(run.out).toMatch(/^3 answer: warn\. At 240px the pointer moves [0-9]% of the ink, .*; under 37% the answer is hard to see in a thumbnail\. /m);
    expect(run.code, run.out).toBe(0);
  });

  test("without an answer point, writes the blind pair and no motion strip", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-look-"));
    const run = await look(cwd, `${SKILL}examples/terrain.js`);
    expect(run.code, run.out).toBe(0);
    expect(run.out).toMatch(/^no --answer: /m);
    expect(run.out).toMatch(/^3 answer: not measured\. No --answer\.$/m);
    wrote(cwd, "hairline-terrain-look.png");
    wrote(cwd, "hairline-terrain-blind.png");
    expect(run.out).toMatch(/^blind .*hairline-terrain-blind\.png holds /m);
    expect(existsSync(join(cwd, "hairline-terrain-motion.png"))).toBe(false);
    expect(run.out).not.toMatch(/^motion /m);
  });

  test("fails a figure that throws when it mounts", async () => {
    const cwd = mkdtempSync(join(tmpdir(), "hl-look-"));
    const src = readFileSync(SKILL + "examples/terrain.js", "utf8").replace(/^(function mount\(.*\{)$/m, '$1\n  throw new Error("no drawing today");');
    expect(src).toContain("no drawing today");
    writeFileSync(join(cwd, "terrain.js"), src);
    const run = await look(cwd, "terrain.js", "--answer", "30,90,0");
    expect(run.code, run.out).toBe(1);
    expect(run.out).toMatch(/^12 console: fail/m);
    expect(run.out).toContain("no drawing today");
  });
});

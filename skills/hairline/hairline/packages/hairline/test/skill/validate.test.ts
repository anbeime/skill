import { execFileSync, spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { same } from "../../../../skills/hairline-create/validate.mjs";

/**
 * validate.mjs passes the two examples and fails a page broken in one way,
 * naming that way and no other. The broken pages are Terrain with one change.
 */
const SKILL = fileURLToPath(new URL("../../../../skills/hairline-create/", import.meta.url));
const dir = mkdtempSync(join(tmpdir(), "hl-validate-"));
const terrain = readFileSync(SKILL + "examples/terrain.js", "utf8");
let n = 0;

/** Builds a figure's page, changes the page if asked, and validates it. */
function check(figure: string, change?: (page: string) => string, script = SKILL + "validate.mjs") {
  const src = join(dir, `f${++n}.js`), out = join(dir, `f${n}.html`);
  writeFileSync(src, figure);
  execFileSync("node", [SKILL + "build.mjs", src, out]);
  if (change) writeFileSync(out, change(readFileSync(out, "utf8")));
  const run = spawnSync("node", [script, out], { encoding: "utf8" });
  return { status: run.status, out: run.stdout, err: run.stderr };
}
/** Terrain with a line of code just before its declaration. */
const plus = (code: string) => terrain.replace("hairline({", () => `${code}\nhairline({`);

describe("pages that pass", () => {
  for (const name of ["terrain", "riffle"]) {
    it(`the ${name} example`, () => {
      const figure = readFileSync(`${SKILL}examples/${name}.js`, "utf8");
      expect(figure.trim().split("\n").length).toBeLessThanOrEqual(200);
      const run = check(figure);
      expect(run.err).toBe("");
      expect(run.status).toBe(0);
      expect(run.out).toMatch(/^ok .*kernel and bench intact/);
    });
  }

  it("a page saved with CRLF line endings", () => {
    expect(check(terrain, (page) => page.replace(/\n/g, "\r\n")).status).toBe(0);
  });

  it("a range that falls, as Slow's does", () => {
    expect(check(terrain.replace("range: [1.5, 3, 5]", "range: [5, 3, 1.5]")).status).toBe(0);
  });

  it("through a symlink to the skill folder", () => {
    const link = join(dir, "linked");
    symlinkSync(SKILL, link);
    const run = check(terrain, undefined, join(link, "validate.mjs"));
    expect(run.status).toBe(0);
    expect(run.out).toMatch(/^ok /);
  });
});

/** Honest code that only looks like a broken rule: a good figure with any of these changes still passes. */
const HONEST: [why: string, figure: string][] = [
  ["an identifier named gradient, for a slope", plus("const gradient = 0.5;")],
  ["a read-out with a number sign", plus('const label = "pillar #101";')],
  ["the word import in a string", plus('const note = "import";')],
  ["the word import inside a longer name", plus("const important = true;")],
  ["a name that starts with import, before a comma", plus("const [important, b] = [1, 2];")],
  ["a name that starts with import, as an argument", plus("f(imported, 1);")],
  ["a tset given a delay of 0, with a call among its values", plus("HL.tset(HL.tween(0), Math.max(1, 2), performance.now(), 0);")],
  ["a name that ends in tset", plus("const offset = (a, b) => a + b;\noffset(1, 2);")],
  ["a tset written in a string", plus('const note = "tset(a, b)";')],
  ["a handle returned in shorthand, { set, destroy }", terrain.replace(
    /return \{\n {4}set: (\(v\) => \{[^\n]*\}),\n {4}destroy: bag\.dispose,\n {2}\};/,
    (_, set) => `const set = ${set};\n  const destroy = bag.dispose;\n  return { set, destroy };`,
  )],
];

describe("honest changes that pass", () => {
  it("each change is made", () => {
    for (const [why, figure] of HONEST) expect(figure, why).not.toBe(terrain);
  });
  for (const [why, figure] of HONEST) {
    it(why, () => {
      const run = check(figure);
      expect(run.err).toBe("");
      expect(run.status).toBe(0);
    });
  }
});

const BROKEN: [id: string, why: string, figure: string, change?: (page: string) => string][] = [
  ["kernel", "the kernel was edited", terrain, (page) => page.replace("var HL = ", "var HL = /* mine */ ")],
  ["bench", "the bench was edited", terrain, (page) => page.replace("</main>", "<p>better</p></main>")],
  ["text", "a text element", plus('mk("text", {}, document.querySelector("svg"));')],
  ["text", "markup written as a string", plus('document.querySelector("svg").innerHTML = "";')],
  ["paint", "a fill of its own", plus('mk("path", { fill: "red" });')],
  ["paint", "a stroke width of its own", plus('mk("path", { "stroke-width": 2 });')],
  ["paint", "an inline style", plus('document.body.style.background = "#000";')],
  ["paint", "a colour in hex", plus('const ink = "#a1b2c3";')],
  ["paint", "an opacity of its own", plus('mk("path", { opacity: 0.5 });')],
  ["paint", "a stroke opacity of its own", plus('mk("path", { "stroke-opacity": 0.5 });')],
  ["paint", "a fill opacity of its own", plus('mk("path", { "fill-opacity": 0.5 });')],
  ["paint", "an opacity set by hand", plus('svg.setAttribute("opacity", "0.5");')],
  ["paint", "a gradient element", plus('mk("linearGradient", {});')],
  ["outside", "a fetch", plus('fetch("https://example.com/data.json");')],
  ["outside", "a node made by hand", plus('document.createElementNS("http://www.w3.org/2000/svg", "path");')],
  ["outside", "a script tag in a string", plus('const s = "</script>";')],
  ["outside", "an import statement", plus('import { x } from "./x.js";')],
  ["outside", "a default import", plus('import x from "./x.js";')],
  ["outside", "a namespace import", plus('import * as x from "./x.js";')],
  ["outside", "a dynamic import", plus('import("./x.js");')],
  ["outside", "a URL in a string", plus('const u = "https://example.com/a.json";')],
  ["clock", "its own frame", plus("requestAnimationFrame(() => {});")],
  ["clock", "its own timer", plus("setTimeout(() => {}, 100);")],
  ["clock", "an SMIL animate element", plus('mk("animate", { dur: "1s", repeatCount: "indefinite" });')],
  ["clock", "an SMIL animateTransform element", plus('mk("animateTransform", { type: "rotate", dur: "1s", repeatCount: "indefinite" });')],
  ["clock", "an SMIL animateMotion element", plus("mk('animateMotion', { dur: \"1s\", repeatCount: \"indefinite\" });")],
  ["clock", "a timer after a // in a string", plus('const s = "a // b"; setTimeout(() => {}, 1);')],
  ["clock", "no kernel loop", terrain.replace("register(stage,", "((s, t) => ({ wake() {}, unregister() {} }))(stage,")],
  ["tween", "a tset without its delay", plus("HL.tset(HL.tween(0), 1, performance.now());")],
  ["tween", "a tset without its delay, with a call among its values", plus("HL.tset(HL.tween(0), Math.max(1, 2), performance.now());")],
  ["hit", "a box measured on screen", plus("stage.getBoundingClientRect();")],
  ["hit", "its own listener", plus('stage.addEventListener("pointermove", () => {});')],
  ["hit", "no pointer", terrain.replace("bag.add(pointer(stage,", "bag.add(((s, h) => () => {})(stage,")],
  ["readout", "no read-out", terrain.replace(/read\.textContent = [^;]+;/g, "")],
  ["handle", "no set, beside a Map's set", plus("new Map().set(1, 2);").replace("set: (v) =>", "put: (v) =>")],
  ["handle", "no destroy", terrain.replace("destroy: bag.dispose", "stop: bag.dispose")],
  ["declare", "no means", terrain.replace(/\n {2}means: .*\n/, "\n")],
  ["declare", "a range that turns back", terrain.replace("range: [1.5, 3, 5]", "range: [1.5, 5, 3]")],
  ["declare", "a rule that does not exist", terrain.replace("rules: [1, 3, 5, 9]", "rules: [1, 11]")],
  ["declare", "no declaration", terrain.replace(/hairline\(\{[\s\S]*$/, "")],
  ["tour", "no tour", terrain.replace(/\n {2}tour: .*\n/, "\n")],
  ["tour", "two stops", terrain.replace(/tour: \[.*\],/, "tour: [[128, 150], null],")],
  ["tour", "seven stops", terrain.replace(/tour: \[.*\],/, "tour: [[10, 10], [20, 20], [30, 30], [40, 40], [50, 50], [60, 60], null],")],
  ["tour", "a stop outside the viewBox", terrain.replace("[272, 150]", "[500, 100]")],
  ["tour", "every stop null", terrain.replace(/tour: \[.*\],/, "tour: [null, null, null],")],
  ["tour", "a figure that starts its own tour", plus("HL.tour(stage, [[1, 2]]);")],
  ["length", "over 200 lines", plus(Array.from({ length: 200 }, (_, i) => `const pad${i} = ${i};`).join("\n"))],  ["parse", "a const declared twice, so the module never loads", plus("const twice = 1;\nconst twice = 2;")],
];

describe("pages that fail, each for its own reason", () => {
  for (const [id, why, figure, change] of BROKEN) {
    it(`${id}: ${why}`, () => {
      const run = check(figure, change);
      expect(run.status).toBe(1);
      const ids = run.err.split("\n").map((line) => /^([a-z]+): /.exec(line)?.[1]).filter(Boolean);
      expect(ids.length).toBeGreaterThan(0);
      expect([...new Set(ids)]).toEqual([id]);
      expect(run.err).toMatch(/\d+ to fix in /);
    });
  }
});

it("says how to call it when it is given nothing, and when the file is not there", () => {
  const none = spawnSync("node", [SKILL + "validate.mjs"], { encoding: "utf8" });
  expect(none.status).toBe(2);
  expect(none.stderr).toContain("usage: node validate.mjs <page.html>");
  const gone = spawnSync("node", [SKILL + "validate.mjs", join(dir, "nope.html")], { encoding: "utf8" });
  expect(gone.status).toBe(2);
  expect(gone.stderr).toContain("cannot read");
});

it("knows a path that differs only in the case of its drive letter is the same path on Windows, and only there", () => {
  expect(same("C:\\x\\validate.mjs", "c:\\x\\validate.mjs", "win32")).toBe(true);
  expect(same("C:\\x\\validate.mjs", "c:\\x\\validate.mjs", "darwin")).toBe(false);
  expect(same("/x/validate.mjs", "/x/validate.mjs", "darwin")).toBe(true);
  expect(same("C:\\x\\validate.mjs", "C:\\x\\validate.mjs", "win32")).toBe(true);
});

it("names the syntax error that stops the figure loading, and its line", () => {
  const run = check(plus("const twice = 1;\nconst twice = 2;"));
  expect(run.status).toBe(1);
  expect(run.err).toContain("Identifier 'twice' has already been declared");
  const line = plus("const twice = 1;\nconst twice = 2;").trim().split("\n").indexOf("const twice = 2;") + 1;
  expect(run.err).toContain(`line ${line}`);
});

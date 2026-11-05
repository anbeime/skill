import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

/** The skill's kernel: generated from src/core, committed, and held current here. */
const ROOT = fileURLToPath(new URL("../../../../", import.meta.url));
const text = () => readFileSync(ROOT + "skills/hairline-create/kernel.js", "utf8");

it("the committed kernel is what src/core gives now", () => {
  const run = spawnSync("node", ["scripts/kernel.mjs", "--check"], { cwd: ROOT, encoding: "utf8" });
  expect(run.stderr).toBe("");
  expect(run.status).toBe(0);
});

it("its first line carries the hash of everything after it", () => {
  const src = text(), cut = src.indexOf("\n");
  const hash = /^\/\* hairline kernel sha256:([0-9a-f]{64}) \*\/$/.exec(src.slice(0, cut))?.[1];
  expect(hash).toBe(createHash("sha256").update(src.slice(cut + 1)).digest("hex"));
  expect(src.endsWith("/* /hairline kernel */\n")).toBe(true);
});

it("defines one global, HL, holding what its index lists and nothing else", () => {
  const src = text();
  const HL = new Function(`${src}\nreturn HL;`)() as Record<string, unknown>;
  const indexed = [...src.slice(0, src.indexOf("var HL")).matchAll(/^ \* {3}(\w+)/gm)].map((m) => m[1]);
  expect(indexed.slice().sort()).toEqual(Object.keys(HL).sort());
  expect(Object.keys(HL)).toHaveLength(46);
  expect(typeof HL.tour).toBe("function");
  expect(Array.isArray(HL.LAP)).toBe(true);
  expect(typeof HL.register).toBe("function");
  expect(typeof HL.EASE_LIFT).toBe("function");
});

it("can sit inside a script element, and is left readable", () => {
  const src = text();
  expect(src).not.toMatch(/<\/script/i);
  expect(src.split("\n").length).toBeGreaterThan(300);
});

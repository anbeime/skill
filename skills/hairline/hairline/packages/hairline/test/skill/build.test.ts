import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";
import { same } from "../../../../skills/hairline-create/build.mjs";

/** build.mjs puts a figure on the bench: the page is the bench, the kernel and the figure, and nothing else. */
const SKILL = fileURLToPath(new URL("../../../../skills/hairline-create/", import.meta.url));
const dir = mkdtempSync(join(tmpdir(), "hl-build-"));
const terrain = readFileSync(SKILL + "examples/terrain.js", "utf8");
const node = (args: string[], cwd = dir) => spawnSync("node", args, { cwd, encoding: "utf8" });

it("writes the bench with the kernel and the figure in their slots", () => {
  const out = join(dir, "page.html");
  const run = node([SKILL + "build.mjs", SKILL + "examples/terrain.js", out]);
  expect(run.stderr).toBe("");
  expect(run.status).toBe(0);
  expect(run.stdout.trim()).toBe(out);
  const page = readFileSync(out, "utf8");
  expect(page).toContain(readFileSync(SKILL + "kernel.js", "utf8").trimEnd());
  expect(page).toContain(terrain.trim());
  expect(page).not.toContain("/*KERNEL*/");
  expect(page).not.toContain("/*FIGURE*/");
});

it("names the page after the figure when no path is given", () => {
  const run = node([SKILL + "build.mjs", SKILL + "examples/terrain.js"]);
  expect(run.status).toBe(0);
  expect(run.stdout.trim().endsWith("hairline-terrain.html")).toBe(true);
  expect(readFileSync(run.stdout.trim(), "utf8")).toContain("<title>");
});

it("names the page from the hairline({ … }) call, not from an earlier name: in the figure", () => {
  const src = join(dir, "tables.js");
  writeFileSync(src, 'const LINES = [{ name: "other", at: 0 }];\n' + terrain);
  const run = node([SKILL + "build.mjs", src]);
  expect(run.status).toBe(0);
  expect(run.stdout.trim()).toMatch(/\/hairline-terrain\.html$/);
});

it("pastes text literally, so a figure may hold $& and $1", () => {
  const src = join(dir, "dollar.js"), out = join(dir, "dollar.html");
  const figure = terrain.replace("hairline({", () => 'const odd = "$& and $1 and $$";\nhairline({');
  writeFileSync(src, figure);
  expect(node([SKILL + "build.mjs", src, out]).status).toBe(0);
  expect(readFileSync(out, "utf8")).toContain('const odd = "$& and $1 and $$";');
});

it("runs when the skill folder is reached through a symlink", () => {
  const link = join(dir, "linked");
  symlinkSync(SKILL, link);
  const out = join(dir, "linked.html");
  const run = node([join(link, "build.mjs"), join(link, "examples/terrain.js"), out]);
  expect(run.status).toBe(0);
  expect(run.stdout.trim()).toBe(out);
});

it("says how to call it when it is given nothing", () => {
  const run = node([SKILL + "build.mjs"]);
  expect(run.status).toBe(2);
  expect(run.stderr).toContain("usage: node build.mjs <figure.js> [out.html]");
});

it("knows a path that differs only in the case of its drive letter is the same path on Windows, and only there", () => {
  expect(same("C:\\x\\build.mjs", "c:\\x\\build.mjs", "win32")).toBe(true);
  expect(same("C:\\x\\build.mjs", "c:\\x\\build.mjs", "darwin")).toBe(false);
  expect(same("/x/build.mjs", "/x/build.mjs", "darwin")).toBe(true);
  expect(same("C:\\x\\build.mjs", "C:\\x\\build.mjs", "win32")).toBe(true);
});

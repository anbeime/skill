import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";

/** The door: one file that sends an SVG to hairline-create's step 0. */
const SKILL = fileURLToPath(new URL("../../../../skills/hairline-adopt/", import.meta.url));
const text = readFileSync(SKILL + "SKILL.md", "utf8");

it("holds exactly its one file", () => {
  expect(readdirSync(SKILL)).toEqual(["SKILL.md"]);
});

it("opens with a name that is its folder's, a description that says when to use it, and an argument hint", () => {
  const m = /^---\nname: (.+)\ndescription: (.+)\nargument-hint: (.+)\n---\n/.exec(text);
  expect(m).not.toBeNull();
  expect(m![1]).toBe("hairline-adopt");
  expect(m![2]).toMatch(/^Use when someone has an SVG/);
  expect(m![2]).toContain("/hairline-adopt");
  expect(m![2].length).toBeLessThanOrEqual(1024);
  expect(m![3]).toBe('"<file.svg> [what the pointer does]"');
});

it("says what it does and does not do, and hands over to /hairline-create by name, never by path", () => {
  expect(text).toMatch(/never animates the SVG itself/);
  expect(text).toMatch(/never traces it/);
  expect(text).toMatch(/one figure at a time/);
  expect(text).toContain("Invoke `/hairline-create`");
  expect(text).toContain("step 0");
  expect(text).not.toMatch(/\.\.\/hairline-create/);
  expect(text).not.toMatch(/`[\w./-]+\.(?:mjs|js|html|md)`/);
  expect(text.split("\n").length).toBeLessThan(40);
});

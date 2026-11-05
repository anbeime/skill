import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { ADOPT, ADOPTED, COMMAND, EXAMPLES, INSTALL, MARKS, declared, examples } from "@/lib/skill";

/**
 * The showcase is the skill's own output: these fail if an example was edited (its hash is pinned in lib/skill.ts),
 * renamed, dropped, or left behind by the kernel (the skill's validator).
 */

const PUBLIC = fileURLToPath(new URL("../public/skill/", import.meta.url));
const VALIDATE = fileURLToPath(new URL("../../../skills/hairline-create/validate.mjs", import.meta.url));

/** The three marks, each the whole line typed after the command. */
const VERCEL = "an empty state for \"No deployments yet\", from Vercel's mark: the triangle as an upright slab hovering over a pad with its slot marked dim; the nearer the pointer, the lower it settles, until it seats. Name it vercel.";
const MASTRA = "an empty state for \"No agents connected\", from Mastra's mark: the spheres of the M joined by necks on a board, the lone sphere standing apart; the pointer draws it toward the others, a neck forms, stretches and lets go. Name it mastra.";
const NOTION = "an empty state for \"No pages inside\", from Notion's mark: the cube as a box with a lid, the N a relief on its front face; the pointer's height opens the lid on a spring, and the box is empty. Name it notion.";

describe("the skill's examples", () => {
  it("are the four ideas, in page order", () => {
    expect(EXAMPLES.map((e) => e.idea)).toEqual(["a sales funnel", "a rate limiter", "git branches", "weather over a city"]);
  });

  it("leave the three marks to the Figures page, which shows them", () => {
    expect(MARKS.map((e) => e.idea)).toEqual([VERCEL, MASTRA, NOTION]);
    expect(MARKS.map((e) => e.file)).toEqual(["hairline-vercel.html", "hairline-mastra.html", "hairline-notion.html"]);
  });

  it("are, with the marks and hairline-adopt's, exactly the files in public/skill", () => {
    expect([...EXAMPLES, ...MARKS, ...ADOPTED].map((e) => e.file).sort()).toEqual(readdirSync(PUBLIC).sort());
  });

  it.each([...EXAMPLES, ...MARKS, ...ADOPTED])("$file is byte for byte the page pinned", ({ file, sha256 }) => {
    expect(createHash("sha256").update(readFileSync(PUBLIC + file)).digest("hex")).toBe(sha256);
  });

  it.each([...EXAMPLES, ...MARKS, ...ADOPTED])("$file passes the skill's validator", ({ file }) => {
    const run = spawnSync(process.execPath, [VALIDATE, PUBLIC + file], { encoding: "utf8" });
    expect(run.stderr).toBe("");
    expect(run.status).toBe(0);
  });

  it("each carry the name their file is called by, a meaning, the prompt and the link", () => {
    for (const e of examples()) {
      expect(e.file).toBe(`hairline-${e.name}.html`);
      expect(e.means.length).toBeGreaterThan(0);
      expect(e.means.length).toBeLessThanOrEqual(140);
      expect(e.prompt).toBe(`${COMMAND} ${e.idea}`);
      expect(e.href).toBe(`/skill/${e.file}`);
    }
  });

  it("carry a follow-up only where the page shown came out of one", () => {
    expect(Object.fromEntries(EXAMPLES.map((e) => [e.idea, e.followUp]))).toEqual({
      "a sales funnel": undefined,
      "a rate limiter": undefined,
      "git branches": "The rails almost disappear and the trains read as loose blocks. Make it read as a railway at a glance.",
      "weather over a city": "The cloud looks like a stack of cylinders. Make it read as a cloud at a glance.",
    });
  });

  it("read the meaning out of the page, escapes undone", () => {
    const page = '<script type="module" id="hl-figure">\nconst tray = { name: "other", means: "not this" };\nhairline({ name: "tiers", means: "A \\"funnel\\" as trays.", rules: [1], range: [0, 1, 2], mount });\n</script>';
    expect(declared(page, "x.html")).toEqual({ name: "tiers", means: 'A "funnel" as trays.' });
  });

  it("refuse a page with no figure in it, naming the file", () => {
    expect(() => declared("<html></html>", "hairline-gone.html")).toThrow(/hairline-gone\.html/);
  });
});

describe("hairline-adopt's examples", () => {
  it("are the rocket and four marks, each an SVG and then what the pointer does", () => {
    expect(ADOPTED.map((e) => e.idea.split(" ")[0])).toEqual(["deploy.svg", "firecrawl.svg", "resend.svg", "linear.svg", "cursor.svg"]);
    for (const e of ADOPTED) expect(e.followUp).toBeUndefined();
  });

  it("each carry their file's name, a meaning, the adopt prompt and the link", () => {
    for (const e of examples(ADOPTED, ADOPT)) {
      expect(e.file).toBe(`hairline-${e.name}.html`);
      expect(e.means.length).toBeGreaterThan(0);
      expect(e.means.length).toBeLessThanOrEqual(140);
      expect(e.prompt).toBe(`${ADOPT} ${e.idea}`);
      expect(e.href).toBe(`/skill/${e.file}`);
    }
  });
});

describe("the skill's commands", () => {
  it("are the ones the skill is installed and called by", () => {
    expect(INSTALL).toBe("npx skills add lucasmarkes/hairline");
    expect(COMMAND).toBe("/hairline-create");
    expect(readFileSync(fileURLToPath(new URL("../../../skills/hairline-create/SKILL.md", import.meta.url)), "utf8")).toContain("name: hairline-create");
    expect(ADOPT).toBe("/hairline-adopt");
    expect(readFileSync(fileURLToPath(new URL("../../../skills/hairline-adopt/SKILL.md", import.meta.url)), "utf8")).toContain("name: hairline-adopt");
  });
});

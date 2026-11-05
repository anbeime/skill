import { describe, expect, it } from "vitest";
import { ENTRIES, NOTICE, SHELVES, spell, tally } from "@/lib/catalogue";
import { FIGURES } from "@/lib/figures";
import { COMMAND, MARKS } from "@/lib/skill";
import { REACT, VANILLA, CDN, paste } from "@/lib/snippets";

describe("the catalogue", () => {
  it("shelves every drawn figure once, with the copy the docs use", () => {
    const drawn = ENTRIES.filter((e) => e.drawn);
    expect(drawn.map((e) => e.id).sort()).toEqual(FIGURES.map((f) => f.id).sort());
    for (const e of drawn) {
      const doc = FIGURES.find((f) => f.id === e.id)!;
      expect([e.name, e.summary, e.stronger]).toEqual([doc.name, doc.summary, doc.stronger]);
    }
  });

  it("names each figure once, on nine shelves", () => {
    expect(new Set(ENTRIES.map((e) => e.id)).size).toBe(ENTRIES.length);
    expect(new Set(ENTRIES.map((e) => e.name)).size).toBe(ENTRIES.length);
    expect(SHELVES.map((s) => s.figures.length)).toEqual([1, 3, 3, 3, 6, 3, 6, 8, 3]);
  });

  it("keeps the marks apart: made by the skill, counted outside the package's tally", () => {
    const marks = SHELVES[SHELVES.length - 1];
    expect([marks.id, marks.figures.map((f) => f.id)]).toEqual(["marks", ["vercel", "mastra", "notion"]]);
    for (const f of marks.figures) {
      expect(f.drawn).toBe(false);
      const made = (f as { made?: { file: string; prompt: string } }).made!;
      const example = MARKS.find((e) => e.file === made.file)!;
      expect(made.prompt).toBe(`${COMMAND} ${example.idea}`);
    }
    // each line says what that page's slider does
    expect(marks.figures.map((f) => f.stronger)).toEqual(["It answers from further away.", "The neck holds further before it lets go.", "The lid opens wider."]);
    expect(tally()).toBe("Eight shelves, thirty-three figures");
    expect(NOTICE).toMatch(/not affiliated/);
  });

  it("counts in words, read from the shelves", () => {
    expect([spell(7), spell(19), spell(20), spell(21), spell(40), spell(99)]).toEqual(["seven", "nineteen", "twenty", "twenty-one", "forty", "ninety-nine"]);
    expect(tally()).toBe("Eight shelves, thirty-three figures");
  });

  it("pastes each figure three ways, and the docs' Terrain is the same as before", () => {
    expect(paste("Terrain", "terrain").map((q) => q.code)).toEqual([REACT, VANILLA, CDN]);
    for (const f of FIGURES) {
      const [react, vanilla, cdn] = paste(f.name, f.id).map((q) => q.code);
      expect(react).toContain(`import { ${f.name} } from "@lucasmarkes/hairline/react"`);
      expect(react).toContain(`<${f.name} />`);
      expect(vanilla).toContain(`${f.id}(document.getElementById("figure")!)`);
      expect(cdn).toContain(`import { ${f.id} } from "https://esm.sh/@lucasmarkes/hairline"`);
    }
  });
});

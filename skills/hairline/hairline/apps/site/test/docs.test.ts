import { gzipSync } from "node:zlib";
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import * as components from "@lucasmarkes/hairline/react";
import * as figures from "@lucasmarkes/hairline";
import type { HairlineOptions } from "@lucasmarkes/hairline";
import { TABLE } from "../../../packages/hairline/src/intensity";
import { NOTICE } from "@/lib/catalogue";
import { SECTIONS } from "@/lib/docs";
import { FIGURES, INTENSITY, OPTIONS, measure } from "@/lib/figures";
import { llms, scale } from "@/lib/llms";
import { tiny } from "@/lib/size";
import { ADOPT, ADOPTED, COMMAND, EXAMPLES, INSTALL } from "@/lib/skill";
import { highlight } from "@/lib/highlight";
import { CDN, CSS, EMPTY, QUICKSTART, REACT, REACT_SIGNATURE, VANILLA, VANILLA_SIGNATURE, install } from "@/lib/snippets";

/** The docs describe the package, and these check that nothing was written by hand around it. */

/* a key added to or taken from HairlineOptions fails the typecheck here, before the table can drift */
const KEYS = { intensity: true, theme: true, label: true, onRead: true, play: true } satisfies Record<keyof HairlineOptions, true>;

describe("the figures", () => {
  it("are the package's, each with a function and a component", () => {
    expect(FIGURES.map((f) => f.id).sort()).toEqual(Object.keys(figures).sort());
    for (const doc of FIGURES) expect(components).toHaveProperty(doc.name);
  });

  it("copy the package's intensity table exactly", () => {
    expect(INTENSITY).toEqual(TABLE);
  });
});

describe("the options table", () => {
  it("has the five keys of HairlineOptions, in that order", () => {
    expect(OPTIONS.map((r) => r.name)).toEqual(Object.keys(KEYS));
  });

  it("gives intensity's default as 0.5", () => {
    expect(OPTIONS[0]).toMatchObject({ name: "intensity", type: "number", default: "0.5" });
  });
});

describe("the install commands", () => {
  it("put npm first and install from the address the site is built for", () => {
    const commands = install("https://example.test");
    expect(commands.map((c) => c.label)).toEqual(["npm", "pnpm", "yarn", "bun", "shadcn"]);
    expect(commands[0].code).toBe("npm i @lucasmarkes/hairline");
    expect(commands[4].code).toBe("npx shadcn@latest add https://example.test/r/hairline.json");
  });
});

describe("the quick start", () => {
  it("pastes React, Vanilla and CDN, each under a file name, and none of them sets an option the package dropped", () => {
    expect(QUICKSTART.map((q) => [q.label, q.file])).toEqual([["React", "app/page.tsx"], ["Vanilla", "main.ts"], ["CDN", "index.html"]]);
    expect(QUICKSTART.map((q) => q.code)).toEqual([REACT, VANILLA, CDN]);
    for (const q of QUICKSTART) expect(q.code).not.toMatch(/stagger|radius|afterglow|coast|bands|labels|ranges|className/);
  });
});

describe("the theme's CSS", () => {
  it("sets all six theme properties", () => {
    for (const key of ["plate", "hi", "edge", "mid", "lo", "stroke"]) expect(CSS).toContain(`--hairline-${key}:`);
  });
});

describe("the signatures", () => {
  it("list the component's five options with their types, read from the options table", () => {
    expect(REACT_SIGNATURE).toBe(`<Terrain
  intensity?: number
  theme?: "auto" | "light" | "dark"
  label?: string
  onRead?: (text: string) => void
  play?: boolean
  {...divProps}
/>
`);
  });

  it("give the function's handle its two methods", () => {
    expect(VANILLA_SIGNATURE).toBe(`terrain(element: HTMLElement, options?: HairlineOptions): {
  update(options: HairlineOptions): void
  destroy(): void
}
`);
  });
});

describe("the Install note's size", () => {
  it("is the gzip size of the vanilla entry, to a tenth of a kB", () => {
    const bytes = gzipSync(readFileSync(new URL("../../../packages/hairline/dist/index.js", import.meta.url))).length;
    expect(tiny()).toBe(`${(bytes / 1000).toFixed(1)} kB`);
    expect(tiny()).toMatch(/^\d+\.\d kB$/);
  });
});

describe("the docs' sections", () => {
  it("are ten, in three groups in order, with unique ids that work as fragments", () => {
    expect(SECTIONS.map((s) => s.id)).toEqual(["install", "quick-start", "options", "empty-states", "react", "vanilla", "cdn", "figures", "theme", "accessibility"]);
    expect(new Set(SECTIONS.map((s) => s.id)).size).toBe(10);
    for (const s of SECTIONS) expect(s.id).toMatch(/^[a-z-]+$/);
    expect(SECTIONS.map((s) => s.group)).toEqual([
      "Getting started", "Getting started", "Getting started", "Getting started",
      "API", "API", "API",
      "Reference", "Reference", "Reference",
    ]);
  });

  it("share their headings with /llms.txt", () => {
    const text = llms("https://example.test");
    for (const title of ["Install", "Options", "Empty states", "Figures", "Theme", "Accessibility"]) {
      expect(SECTIONS.map((s) => s.title)).toContain(title);
      expect(text).toContain(`\n## ${title}\n`);
    }
  });
});

describe("the intensity table", () => {
  it("writes each number with its unit, as /llms.txt does", () => {
    expect(measure(40, "ms")).toBe("40 ms");
    expect(measure(0.2, "× normal speed")).toBe("0.2× normal speed");
    for (const doc of FIGURES) {
      const [lo, mid, hi] = INTENSITY[doc.id].map((n) => measure(n, doc.parameter.unit));
      expect(scale(doc.id, doc.parameter)).toBe(`${doc.parameter.name} ${lo} at 0, ${mid} at 0.5, ${hi} at 1`);
    }
  });
});

describe("/llms.txt", () => {
  const text = llms("https://example.test");

  it("says how to install the skill and links each example, with its follow-up, to the page it produced", () => {
    expect(text).toContain("## Make your own");
    expect(text).toContain(INSTALL);
    for (const e of EXAMPLES) expect(text).toContain(`- \`${COMMAND} ${e.idea}\`${e.followUp ? `, then "${e.followUp}"` : ""}: https://example.test/skill/${e.file}`);
    // the two pages a follow-up made say so
    expect(text).toContain(`- \`${COMMAND} git branches\`, then "The rails almost disappear`);
    expect(text).toContain(`- \`${COMMAND} weather over a city\`, then "The cloud looks like a stack of cylinders`);
    expect(text).toContain("https://example.test/skills\n");
    expect(text.indexOf("## Make your own")).toBeLessThan(text.indexOf("## Links"));
  });

  it("says, right after hairline-adopt's examples, which start from companies' marks, that the marks are their owners'", () => {
    expect(text).toContain(`https://example.test/skill/${ADOPTED.at(-1)!.file}\n\n${NOTICE}\n`);
    expect(text.split(NOTICE)).toHaveLength(2);
  });

  it("says how to start from an SVG and links each of hairline-adopt's examples to its page", () => {
    expect(text).toContain(`type \`${ADOPT} <file.svg>\``);
    for (const e of ADOPTED) expect(text).toContain(`- \`${ADOPT} ${e.idea}\`: https://example.test/skill/${e.file}`);
  });

  it.each(FIGURES)("names $name with its row of the intensity table", (doc) => {
    expect(text).toContain(`### ${doc.name}`);
    expect(text).toContain(doc.stronger);
    expect(text).toContain(scale(doc.id, doc.parameter));
    for (const n of INTENSITY[doc.id]) expect(scale(doc.id, doc.parameter)).toContain(String(n));
  });

  it("documents the five options, every theme property and the registry item", () => {
    for (const row of OPTIONS) expect(text).toContain(`- \`${row.name}\``);
    for (const key of ["plate", "hi", "edge", "mid", "lo", "stroke"]) expect(text).toContain(`--hairline-${key}`);
    expect(text).toContain("https://example.test/r/hairline.json");
  });

  it("mentions no option the package dropped", () => {
    expect(text).not.toMatch(/stagger=|radius=|\bbands\b|\blabels\b|\branges\b/);
  });

  it("has no hole in it", () => {
    // outside the code blocks, where `undefined` is a word TypeScript uses
    const prose = text.replace(/```[\s\S]*?```/g, "").replace(/`undefined`/g, "");
    expect(prose).not.toMatch(/undefined|NaN|\[object/);
  });
});

/** Every snippet the docs highlight, with its language. */
const SAMPLES: [code: string, lang: string][] = [[REACT, "tsx"], [VANILLA, "ts"], [CDN, "html"], [CSS, "css"], [REACT_SIGNATURE, "tsx"], [VANILLA_SIGNATURE, "ts"], [EMPTY, "tsx"]];

describe("highlighting", () => {
  it("colours tokens with the --code- variables only, and leaves the block one tab stop", async () => {
    for (const [code, lang] of SAMPLES) {
      const html = await highlight(code, lang);
      expect(html).toContain("var(--code-");
      // the CSS sample holds #ffffff as text, so only colours set in a style count
      expect(html).not.toMatch(/(?:color|background-color):\s*#/i);
      expect(html).not.toContain("tabindex");
    }
  });

  it("writes only variables globals.css defines", async () => {
    const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
    const used = new Set<string>();
    for (const [code, lang] of SAMPLES) for (const m of (await highlight(code, lang)).matchAll(/var\((--code-[a-z-]+)\)/g)) used.add(m[1]);
    expect(used.size).toBeGreaterThan(3);
    for (const name of used) expect(css).toContain(`${name}:`);
  });
});

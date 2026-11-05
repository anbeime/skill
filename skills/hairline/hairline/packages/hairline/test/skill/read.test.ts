import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";
import { card, light, nameFor, page, relate, scan } from "../../../../skills/hairline-create/read.mjs";

const FIX = fileURLToPath(new URL("./fixtures/", import.meta.url));
const svg = (f: string) => readFileSync(FIX + f, "utf8");

/** nameFor: a name build.mjs accepts, from --name or the file name. */
it("takes the name from the file, lowercased and hyphenated, or from --name", () => {
  expect(nameFor("icons/deploy.svg")).toBe("deploy");
  expect(nameFor("My Icon.svg")).toBe("my-icon");
  expect(nameFor("3d-box.svg")).toBe("x3d-box");
  expect(nameFor("a__b..c.svg")).toBe("a-b-c");
  expect(nameFor("deploy.svg", "Rocket")).toBe("rocket");
});

/** scan: what the XML alone says. */
it("reads the viewBox, the title, the ids, the groups and the counts of an icon", () => {
  const info = scan(svg("rocket.svg"), "rocket.svg");
  expect(info).toMatchObject({
    file: "rocket.svg", viewBox: [0, 0, 24, 24], synthesised: false, title: "Deploy",
    ids: ["rocket", "body", "window", "fin-left", "fin-right", "flame"], groups: 2,
    counts: { path: 4, circle: 1 }, notRead: {},
  });
});

it("reads a logo of paths with no title and no ids", () => {
  const info = scan(svg("mark.svg"), "mark.svg");
  expect(info).toMatchObject({ viewBox: [0, 0, 100, 100], title: null, ids: [], groups: 0, counts: { path: 3 }, notRead: {} });
  expect(card(info)).toContain("title: none   ids: none");
});

it("synthesises a viewBox from width and height, skips <defs>, and lists what it does not read", () => {
  const info = scan(svg("mixed.svg"), "mixed.svg");
  expect(info.viewBox).toEqual([0, 0, 48, 32]);
  expect(info.synthesised).toBe(true);
  /* the rect under <defs> and the circle under <symbol> are not painted */
  expect(info.counts).toEqual({ rect: 1 });
  /* a <use> inside the file is a shape by reference; one pointing outside, text and image are not read */
  expect(info.notRead).toEqual({ use: 1, text: 1, image: 1 });
});

it("refuses what has no size and what is not an SVG", () => {
  expect(scan('<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>', "x.svg")).toEqual({ error: "x.svg has no viewBox and no width and height: the card cannot be measured" });
  expect(scan(svg("broken.txt"), "broken.txt")).toEqual({ error: "broken.txt is not an SVG: no <svg> root" });
});

/** relate: one relation per shape, from the boxes alone. */
const ink = { x: 5, y: 2, w: 14, h: 20 };
const S = (i: number, x: number, y: number, w: number, h: number) => ({ i, type: "path", group: null, box: { x, y, w, h }, filled: true, stroke: null, closed: true, kind: "lines" });
it("says inside and where, above or below, left or right, and mirror of", () => {
  const body = S(1, 8, 2, 8, 15), win = S(2, 10.5, 7, 3, 3), finL = S(3, 5, 12, 3, 5), finR = S(4, 16, 12, 3, 5), flame = S(5, 10, 17, 4, 5);
  expect(relate([body, win, finL, finR, flame], ink)).toEqual([
    "",
    "inside #1, middle",
    "left of #1, touching",
    "mirror of #3",
    "below #1, touching",
  ]);
});

it("says nothing for a shape apart from every other", () => {
  expect(relate([S(1, 0, 0, 2, 2), S(2, 50, 50, 2, 2)], { x: 0, y: 0, w: 52, h: 52 })).toEqual(["", ""]);
});

/** card: the text the agent reads. */
it("writes the reduced card from a scan, and says the picture was not taken", () => {
  const text = card(scan(svg("mixed.svg"), "mixed.svg"));
  expect(text.split("\n")[0]).toBe("mixed.svg  viewBox 0 0 48 32 (from width and height)  (1.5:1)  1 shape in 0 groups");
  expect(text).toContain("title: none   ids: clip, dot");
  expect(text).toContain("shapes: 1 rect");
  expect(text).toContain("not read: 1 <use> outside the file, 1 <text>, 1 <image>");
  expect(text).toContain("no browser: boxes and the picture were not taken; read the SVG's own text for them");
});

it("writes the full card with one line per shape, small shapes counted, and 30 lines at most", () => {
  const info = scan(svg("rocket.svg"), "rocket.svg");
  const shapes = [
    { i: 1, type: "path", group: "rocket", box: { x: 8, y: 2, w: 8, h: 15 }, filled: false, stroke: 1.5, closed: true, kind: "curves and lines" },
    { i: 2, type: "circle", group: "rocket", box: { x: 10.5, y: 7, w: 3, h: 3 }, filled: true, stroke: null, closed: true, kind: "curves" },
    { i: 3, type: "path", group: "rocket", box: { x: 5, y: 12, w: 3, h: 5 }, filled: false, stroke: 1.5, closed: true, kind: "lines" },
    { i: 4, type: "path", group: "rocket", box: { x: 16, y: 12, w: 3, h: 5 }, filled: false, stroke: 1.5, closed: true, kind: "lines" },
    { i: 5, type: "path", group: "flame", box: { x: 10, y: 17, w: 4, h: 5 }, filled: true, stroke: null, closed: true, kind: "curves and lines" },
    { i: 6, type: "circle", group: null, box: { x: 0, y: 0, w: 0.1, h: 0.1 }, filled: true, stroke: null, closed: true, kind: "curves" },
  ];
  const text = card(info, shapes);
  const lines = text.split("\n");
  expect(lines[0]).toBe("rocket.svg  viewBox 0 0 24 24  (1:1)  6 shapes in 2 groups");
  expect(lines[1]).toBe("title: \"Deploy\"   ids: rocket, body, window, fin-left, fin-right, flame");
  expect(lines[2]).toBe("ink: 5..19 × 2..22  (58% × 83% of the viewBox)");
  expect(text).toMatch(/^#1 +path +g#rocket +box 8\.\.16 × 2\.\.17  centre 12,9\.5  stroke 1\.5  closed, curves and lines  \(tall, 1:1\.9\)$/m);
  expect(text).toMatch(/^#2 +circle +g#rocket +box 10\.5\.\.13\.5 × 7\.\.10  centre 12,8\.5  filled  closed, curves  inside #1, middle$/m);
  expect(text).toMatch(/^#4 +path +g#rocket +box 16\.\.19 × 12\.\.17  centre 17\.5,14\.5  stroke 1\.5  closed, lines  mirror of #3$/m);
  expect(text).toContain("and 1 small shape");
  expect(lines.length).toBeLessThanOrEqual(30);
  /* forty shapes: the card lists some and counts the rest */
  const many = Array.from({ length: 40 }, (_, k) => ({ ...shapes[0], i: k + 1, box: { x: k, y: 2, w: 8, h: 15 } }));
  const long = card(info, many).split("\n");
  expect(long.length).toBeLessThanOrEqual(30);
  expect(long.at(-1)).toMatch(/^and \d+ more shapes$/);
});

/** Findings of the final review: each pins one failure on a real SVG. */
it("keeps the not-read line on a busy card, under the 30 lines", () => {
  const info = { ...scan(svg("rocket.svg"), "rocket.svg"), notRead: { text: 1 } };
  const rects = Array.from({ length: 30 }, (_, k) => ({ i: k + 1, type: "rect", group: null, box: { x: k * 3, y: 0, w: 2, h: 40 }, filled: true, stroke: null, closed: true, kind: "lines" }));
  const speck = { ...rects[0], i: 31, box: { x: 0, y: 0, w: 0.1, h: 0.1 } };
  const lines = card(info, [...rects, speck]).split("\n");
  expect(lines.length).toBeLessThanOrEqual(30);
  expect(lines).toContain("not read: 1 <text>");
  expect(lines).toContain("and 1 small shape");
});

it("takes width and height in px or absolute units, and refuses % and font units", () => {
  const root = (w: string, h: string) => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}"><rect width="1" height="1"/></svg>`;
  expect(scan(root("24px", "12px"), "a.svg").viewBox).toEqual([0, 0, 24, 12]);
  expect(scan(root("1in", "0.5in"), "a.svg").viewBox).toEqual([0, 0, 96, 48]);
  expect(scan(root("100%", "100%"), "a.svg")).toEqual({ error: "a.svg has no viewBox, and its width and height are in %: the card cannot be measured" });
  expect(scan(root("2em", "2em"), "a.svg")).toEqual({ error: "a.svg has no viewBox, and its width and height are in em: the card cannot be measured" });
});

it("drops a DOCTYPE with an internal subset whole, so nothing of it lands in the picture", () => {
  const html = page(svg("illustrator.svg"), [0, 0, 100, 100]);
  expect(html).not.toContain("]>");
  expect(html).not.toContain("ENTITY");
});

/** Found on a real logo: ink of #FDFDFD vanished on the white picture. */
it("calls the ink light by its colours, weighted by each shape's box", () => {
  const C = (colour: string | null, w: number) => ({ ...S(1, 0, 0, w, w), colour });
  expect(light([C("rgb(253, 253, 253)", 10)])).toBe(true);
  expect(light([C("rgb(24, 24, 27)", 10)])).toBe(false);
  /* a large dark shape with a small light one inside is dark ink */
  expect(light([C("rgb(0, 0, 0)", 10), C("rgb(255, 255, 255)", 3)])).toBe(false);
  /* a white tile carrying a dark glyph is light ink: on white the tile would vanish */
  expect(light([C("rgb(255, 255, 255)", 10), C("rgb(0, 0, 0)", 3)])).toBe(true);
  /* a gradient or nothing known: white, as before */
  expect(light([C(null, 10)])).toBe(false);
  expect(light([])).toBe(false);
});

it("draws the picture on dark when asked, and on white otherwise", () => {
  expect(page(svg("mark.svg"), [0, 0, 100, 100])).toContain("background:#fff");
  const dark = page(svg("mark.svg"), [0, 0, 100, 100], true);
  expect(dark).toContain("background:#18181b");
  expect(dark).not.toContain("background:#fff");
});

it("says on the ink line when the picture is on dark", () => {
  const info = scan(svg("mark.svg"), "mark.svg");
  const shapes = [S(1, 10, 10, 80, 80)];
  expect(card(info, shapes).split("\n")[2]).toBe("ink: 10..90 × 10..90  (80% × 80% of the viewBox)");
  expect(card(info, shapes, true).split("\n")[2]).toBe("ink: 10..90 × 10..90  (80% × 80% of the viewBox)  light ink: the picture is on dark");
});

/** Found on a real logo: one <path> of three subpaths was one shape on the card. */
it("names each part of a path drawn in several pieces", () => {
  const info = scan(svg("mark.svg"), "mark.svg");
  const parts = [{ ...S(1, 2, 2, 6, 6), part: "1 of 2" }, { ...S(2, 12, 2, 6, 6), part: "2 of 2" }];
  expect(card(info, parts)).toMatch(/^#2 +path .* closed, lines, part 2 of 2/m);
});

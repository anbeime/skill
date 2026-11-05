import { test } from "node:test";
import assert from "node:assert/strict";
import { FORMATS, PAPER, boxOf, detailedPlan, fitAspect, focusCrop, layerTable, pagesOf, relax, sheetHtml } from "./print-sheet.mjs";
import { captureScript } from "./print.mjs";

const layer = (id) => `<g class="it" data-print-part="${id}" style="--anatomy-hi:var(--on-${id}-hi,var(--part-hi,#26262a));display:var(--show-${id},inline)"><path d="M0 0L10 10"/></g>`;

function fakeCapture() {
  const view = {
    vb: [0, 0, 400, 600],
    content: [20, 20, 360, 560],
    layers: [`<path d="M0 0L400 600"/>`, layer("pump") + layer("bell") + layer("frame")],
    boxes: { pump: [100, 100, 180, 160], bell: [120, 300, 260, 520], frame: [0, 0, 400, 40] },
    anchors: { pump: [140, 130], bell: [190, 410], frame: [200, 20] },
  };
  return {
    css: ".iso-line{stroke:#000}",
    views: {
      rest: view,
      apart: { ...view, layers: [view.layers[0], layer("pump") + layer("bell")] },
      fire: { vb: [0, 0, 400, 600], layers: [], boxes: {}, anchors: {}, raster: { region: [50, 50, 300, 400], href: "data:image/png;base64,AAAA" } },
    },
  };
}

const SPEC = {
  name: "Test engine",
  title: "Test engine: how it works",
  number: "AN-900",
  tagline: "A test",
  question: "How does it work?",
  lead: "It pumps, then it burns.",
  quote: "One line",
  numbers: [["1", "x", "one"], ["2", "y", "two"]],
  spec: [["Mass", "1 kg"]],
  why: { title: "Why?", text: "Because." },
  parts: [
    { id: "pump", name: "Pump", say: "Raises the pressure." },
    { id: "bell", name: "Bell", say: "Turns pressure into speed." },
    { id: "frame" },
  ],
  main: { view: "apart" },
  inset: { label: "Assembled", view: "rest" },
  steps: [
    { view: "apart", title: "Pump", text: "It pumps.", focus: ["pump"] },
    { view: "apart", title: "Bell", text: "It burns.", focus: ["bell"], hide: ["frame"] },
    { view: "fire", title: "Fire", text: "It fires." },
  ],
  details: [{ title: "The pump", text: "Close up.", around: ["pump"], focus: ["pump"] }],
};

test("fitAspect keeps the box and reaches the aspect", () => {
  for (const aspect of [0.5, 1, 2.4]) {
    const [x, y, w, h] = fitAspect([10, 20, 100, 50], aspect);
    assert.ok(Math.abs(w / h - aspect) < 0.01);
    assert.ok(x <= 10 && y <= 20 && x + w >= 110 && y + h >= 70);
  }
});

test("boxOf unions part boxes and throws on unknown parts", () => {
  const view = fakeCapture().views.rest;
  assert.deepEqual(boxOf(view, ["pump", "bell"]), [100, 100, 160, 420]);
  assert.throws(() => boxOf(view, ["nope"]), /no boxes/);
});

test("focusCrop has the asked aspect and stays inside a larger frame", () => {
  const view = fakeCapture().views.rest;
  const frame = [0, 0, 400, 600];
  const [x, y, w, h] = focusCrop(view, ["pump"], 1, frame);
  assert.ok(Math.abs(w / h - 1) < 0.01);
  assert.ok(x >= 0 && y >= 0 && x + w <= 400.1 && y + h <= 600.1);
  assert.ok(x <= 100 && x + w >= 180);
});

test("relax pushes pins apart to the gap and keeps distant pins still", () => {
  const out = relax([{ n: 1, at: [0, 0] }, { n: 2, at: [1, 0] }, { n: 3, at: [1, 1] }, { n: 4, at: [100, 100] }], 10);
  for (let i = 0; i < 3; i++) for (let j = i + 1; j < 3; j++) assert.ok(Math.hypot(out[i].pos[0] - out[j].pos[0], out[i].pos[1] - out[j].pos[1]) >= 9.99);
  assert.deepEqual(out[3].pos, [100, 100]);
});

test("layerTable stores a layer shared by two views once", () => {
  const { defs, refs } = layerTable(fakeCapture().views);
  assert.equal(refs.rest[0], refs.apart[0]);
  assert.notEqual(refs.rest[1], refs.apart[1]);
  assert.equal((defs.match(/<g id="pl/g) ?? []).length, 3);
});

test("every format renders its pages, numbered pins and the named parts only", () => {
  for (const format of FORMATS) {
    const html = sheetHtml(fakeCapture(), SPEC, PAPER.a4, format);
    assert.equal((html.match(/<main class="ps /g) ?? []).length, pagesOf(format), format);
    assert.match(html, /@page\{size:210mm 297mm/);
    const pins = [...html.matchAll(/class="ps-pin" style="[^"]*">(\d+)</g)].map((m) => m[1]);
    assert.deepEqual(pins, ["1", "2"], format);
    assert.ok(html.includes("Pump") && html.includes("Bell"));
    assert.ok(!/https?:\/\//.test(html.replace(/xmlns="http:\/\/www\.w3\.org\/2000\/svg"/g, "")), `${format} reaches outside the page`);
  }
});

test("focus lights the asked parts, dims the rest and hide removes a part", () => {
  const html = sheetHtml(fakeCapture(), SPEC, PAPER.a4, "drawing");
  assert.match(html, /--part-hi:#cdcdd1;[^"]*--on-pump-hi:#000000/);
  assert.match(html, /--on-bell-hi:#000000;[^"]*--show-frame:none/);
  assert.match(html, /<image href="data:image\/png;base64,AAAA" x="50" y="50" width="300" height="400"/);
});

test("the detailed format marks close-ups on the figure and adds the why", () => {
  const html = sheetHtml(fakeCapture(), SPEC, PAPER.a4, "detailed");
  assert.match(html, /class="ps-mark"/);
  assert.match(html, /ps-letter[^>]*>A</);
  assert.ok(html.includes("Because."));
});

test("Letter paper changes the page size and unknown formats throw", () => {
  assert.match(sheetHtml(fakeCapture(), SPEC, PAPER.letter, "poster"), /@page\{size:215\.9mm 279\.4mm/);
  assert.throws(() => sheetHtml(fakeCapture(), SPEC, PAPER.a4, "zine"), /unknown format/);
});

test("captureScript is one expression that carries the part selectors", () => {
  const script = captureScript({ parts: [{ id: "pump", name: "Pump", select: '[data-name^="pump"]' }, { id: "x", name: "X" }], strip: [".glow"] });
  assert.doesNotThrow(() => new Function(`return ${script}`));
  assert.ok(script.includes('[data-name^=\\"pump\\"]'));
  assert.ok(script.includes(".glow"));
  assert.ok(!script.includes('"id":"x"'));
});

test("detailed grows from 2 to 4 pages with steps and assemblies, under a cap", () => {
  const steps = (n) => Array.from({ length: n }, (_, i) => ({ title: `s${i}` }));
  const asm = (n) => Array.from({ length: n }, (_, i) => ({ title: `a${i}`, parts: ["pump"] }));
  assert.equal(detailedPlan({ steps: steps(5), why: { title: "w", text: "t" } }).total, 2);
  assert.equal(detailedPlan({ steps: steps(5), assemblies: asm(4) }).total, 3);
  assert.equal(detailedPlan({ steps: steps(9), assemblies: asm(4) }).total, 4);
  assert.equal(detailedPlan({ steps: steps(9), assemblies: asm(8) }).total, 4);
  assert.equal(detailedPlan({ steps: steps(5), assemblies: asm(4), maxPages: 2 }).total, 2);
  assert.throws(() => detailedPlan({ steps: steps(19) }), /over maxPages/);
  const html = sheetHtml(fakeCapture(), { ...SPEC, assemblies: [{ title: "Pump group", parts: ["pump"] }] }, PAPER.a4, "detailed");
  assert.equal((html.match(/<main class="ps /g) ?? []).length, 3);
  assert.ok(html.includes("Assemblies") && html.includes("1 / 3"));
});

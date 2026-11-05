#!/usr/bin/env node
/**
 * Reads an SVG the person already has, for a figure built from it:
 *
 *   node <skill folder>/read.mjs <file.svg> [--name <name>]
 *
 * It writes, in the working directory, hairline-<name>-source.png, the SVG
 * drawn at 400 × 400 on white, or on dark when its ink is light, and
 * hairline-<name>-source.txt, the card: the viewBox, the title and ids, the
 * ink's box, and one line per painted shape, each piece of a path drawn in
 * several counted as one, with its type, group, box, centre, fill or stroke,
 * and its relation to the shape it sits in or touches. source.md says how to read it. The boxes come
 * from the browser look.mjs installs; without one the card is reduced to what
 * the XML says, and no picture is written. The SVG gives the identity, not
 * the paths: nothing here is traced.
 */
import { readFileSync, realpathSync, writeFileSync } from "node:fs";
import { basename, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

const here = (p) => fileURLToPath(new URL(p, import.meta.url));
const USAGE = "usage: node read.mjs <file.svg> [--name <name>]";
/* look.mjs imports this file while it runs, so this file takes look.mjs only inside read(), and compares paths itself */
const same = (a, b, platform = process.platform) => platform === "win32" ? a.toLowerCase() === b.toLowerCase() : a === b;

/** The card lists this many shapes at most, so that with the more, small and not-read lines it stays within 30. */
const LISTED = 23;
/** A shape smaller than this share of the ink's box, both ways, is counted, not listed. */
const SMALL = 0.02;
/** Boxes this close, as a share of the ink's size, touch; a mirror matches within it too. */
const NEAR = 0.05;
/** Ink whose mean luminance is above this is drawn on dark: on white it would vanish. */
const LIGHT = 0.5;

const SHAPES = ["path", "rect", "circle", "ellipse", "line", "polyline", "polygon"];
const UNREAD = ["text", "image", "foreignObject"];
/** Elements whose children are not painted where they stand. */
const HIDDEN = ["defs", "symbol", "clipPath", "mask", "pattern", "marker"];

/**
 * A name build.mjs accepts: --name, else the file's, lowercased, runs of anything else as one hyphen, a digit first prefixed with x.
 * @param {string} file
 * @param {string | null} [given]
 */
export function nameFor(file, given = null) {
  const raw = (given ?? basename(file).replace(/\.svg$/i, "")).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  return /^[a-z]/.test(raw) ? raw : `x${raw}`;
}

/** The tags of an SVG in order, with their attributes; comments, CDATA and declarations skipped. Enough to count, never to draw. */
function tags(xml) {
  const out = [];
  const re = /<!--[\s\S]*?-->|<!\[CDATA\[[\s\S]*?\]\]>|<[?!][\s\S]*?>|<\/([\w:.-]+)\s*>|<([\w:.-]+)((?:\s+[\w:.-]+\s*=\s*(?:"[^"]*"|'[^']*'))*)\s*(\/?)>/g;
  for (let m; (m = re.exec(xml));) {
    if (m[1]) out.push({ close: m[1] });
    else if (m[2]) {
      const attrs = {};
      for (const a of m[3].matchAll(/([\w:.-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g)) attrs[a[1]] = a[2] ?? a[3];
      out.push({ open: m[2], attrs, self: !!m[4] });
    }
  }
  return out;
}

/** CSS pixels per unit, for the absolute units a width or height can carry. */
const PX = { "": 1, px: 1, in: 96, cm: 96 / 2.54, mm: 96 / 25.4, pt: 4 / 3, pc: 16 };
/** A length attribute: its value in px, or its unit when it is relative (%, em, ex…), or null when it is not one. */
const len = (v) => {
  const m = /^\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)\s*([a-z%]*)\s*$/i.exec(v ?? "");
  if (!m) return null;
  const unit = m[2].toLowerCase();
  return unit in PX ? Number(m[1]) * PX[unit] : unit;
};

/** What the XML alone says of the SVG. An object with `error` when it cannot be read as one. */
export function scan(xml, fileName) {
  const list = tags(xml);
  const root = list.find((t) => t.open === "svg");
  if (!root) return { error: `${fileName} is not an SVG: no <svg> root` };
  let viewBox = (root.attrs.viewBox ?? "").trim().split(/[\s,]+/).map(Number);
  let synthesised = false;
  if (viewBox.length !== 4 || !viewBox.every(Number.isFinite) || !(viewBox[2] > 0 && viewBox[3] > 0)) {
    const w = len(root.attrs.width), h = len(root.attrs.height);
    const relative = [w, h].find((v) => typeof v === "string");
    if (relative) return { error: `${fileName} has no viewBox, and its width and height are in ${relative}: the card cannot be measured` };
    if (!(w > 0) || !(h > 0)) return { error: `${fileName} has no viewBox and no width and height: the card cannot be measured` };
    viewBox = [0, 0, w, h];
    synthesised = true;
  }
  const ids = [], counts = {}, notRead = {}, open = [];
  let groups = 0;
  const title = /<title[^>]*>([\s\S]*?)<\/title>/.exec(xml)?.[1].trim() || null;
  for (const t of list) {
    if (t.close) { open.pop(); continue; }
    if (t.attrs.id) ids.push(t.attrs.id);
    const hidden = open.some((o) => HIDDEN.includes(o)) || HIDDEN.includes(t.open);
    if (!t.self) open.push(t.open);
    if (hidden) continue;
    if (t.open === "g") groups++;
    else if (SHAPES.includes(t.open)) counts[t.open] = (counts[t.open] ?? 0) + 1;
    else if (UNREAD.includes(t.open)) notRead[t.open] = (notRead[t.open] ?? 0) + 1;
    else if (t.open === "use" && !(t.attrs.href ?? t.attrs["xlink:href"] ?? "").startsWith("#")) notRead.use = (notRead.use ?? 0) + 1;
  }
  return { file: fileName, viewBox, synthesised, title, ids, groups, counts, notRead };
}

const r1 = (v) => Math.round(v * 10) / 10;
const span = (b) => `${r1(b.x)}..${r1(b.x + b.w)} × ${r1(b.y)}..${r1(b.y + b.h)}`;
const centre = (b) => [b.x + b.w / 2, b.y + b.h / 2];
const area = (b) => b.w * b.h;
const inside = (a, b) => a.x >= b.x - 1e-6 && a.y >= b.y - 1e-6 && a.x + a.w <= b.x + b.w + 1e-6 && a.y + a.h <= b.y + b.h + 1e-6 && area(a) < area(b);

/** One relation per shape, read from the boxes: inside the largest shape that holds it; else the mirror of an earlier shape; else touching the largest it touches; else nothing. */
export function relate(shapes, ink) {
  const near = NEAR * Math.max(ink.w, ink.h);
  const gap = (a, b) => Math.max(b.x - (a.x + a.w), a.x - (b.x + b.w), 0) + Math.max(b.y - (a.y + a.h), a.y - (b.y + b.h), 0);
  const side = (a, b) => {
    const [ax, ay] = centre(a), [bx, by] = centre(b);
    return Math.abs(ax - bx) * b.h >= Math.abs(ay - by) * b.w ? (ax < bx ? "left of" : "right of") : (ay < by ? "above" : "below");
  };
  const third = (a, b) => { const k = (centre(a)[1] - b.y) / b.h; return k < 1 / 3 ? "upper third" : k > 2 / 3 ? "lower third" : "middle"; };
  const axis = ink.x + ink.w / 2;
  return shapes.map((s) => {
    const others = shapes.filter((o) => o !== s);
    const holder = others.filter((o) => inside(s.box, o.box)).sort((a, b) => area(b.box) - area(a.box))[0];
    if (holder) return `inside #${holder.i}, ${third(s.box, holder.box)}`;
    const mirror = others.find((o) => o.i < s.i && Math.abs(o.box.w - s.box.w) <= near && Math.abs(o.box.h - s.box.h) <= near
      && Math.abs(o.box.y - s.box.y) <= near && Math.abs(axis - centre(o.box)[0] - (centre(s.box)[0] - axis)) <= near
      && Math.abs(centre(s.box)[0] - axis) > near);
    if (mirror) return `mirror of #${mirror.i}`;
    const touched = others.filter((o) => area(o.box) > area(s.box) && gap(s.box, o.box) <= near).sort((a, b) => area(b.box) - area(a.box))[0];
    if (touched) return `${side(s.box, touched.box)} #${touched.i}, touching`;
    return "";
  });
}

/**
 * Whether the ink is light: the luminance of each shape's colour, weighted by its box. A colour that is not plain (a gradient) is left out.
 * @param {any[]} shapes
 */
export function light(shapes) {
  const lin = (c) => (c /= 255) <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  let sum = 0, weight = 0;
  for (const s of shapes) {
    const c = /rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)/.exec(s.colour ?? "");
    if (!c) continue;
    const w = Math.max(area(s.box), 1e-6);
    sum += w * (0.2126 * lin(+c[1]) + 0.7152 * lin(+c[2]) + 0.0722 * lin(+c[3]));
    weight += w;
  }
  return weight > 0 && sum / weight > LIGHT;
}

/** The box round a list of boxes. */
const union = (boxes) => {
  const x0 = Math.min(...boxes.map((b) => b.x)), y0 = Math.min(...boxes.map((b) => b.y));
  return { x: x0, y: y0, w: Math.max(...boxes.map((b) => b.x + b.w)) - x0, h: Math.max(...boxes.map((b) => b.y + b.h)) - y0 };
};
const ratio = (w, h) => (w >= h ? `${r1(w / h)}:1` : `1:${r1(h / w)}`);
const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
const pad = (s, n) => String(s).padEnd(n);

/**
 * The card. With `shapes` null it is the reduced card: what scan() read, and a line saying the rest was not taken.
 * @param {any} info
 * @param {any[] | null} [shapes]
 * @param {boolean} [dark] the picture was taken on dark
 */
export function card(info, shapes = null, dark = false) {
  const [vx, vy, vw, vh] = info.viewBox;
  const total = shapes ? shapes.length : Object.values(info.counts).reduce((a, b) => a + b, 0);
  const lines = [
    `${info.file}  viewBox ${vx} ${vy} ${vw} ${vh}${info.synthesised ? " (from width and height)" : ""}  (${ratio(vw, vh)})  ${plural(total, "shape")} in ${plural(info.groups, "group")}`,
    `title: ${info.title ? `"${info.title}"` : "none"}   ids: ${info.ids.length ? info.ids.join(", ") : "none"}`,
  ];
  const unread = Object.entries(info.notRead).map(([k, n]) => `${n} <${k}>${k === "use" ? " outside the file" : ""}`);
  if (!shapes) {
    lines.push(`shapes: ${Object.entries(info.counts).map(([k, n]) => `${n} ${k}`).join(", ") || "none"}`);
    if (unread.length) lines.push(`not read: ${unread.join(", ")}`);
    lines.push("no browser: boxes and the picture were not taken; read the SVG's own text for them");
    return lines.join("\n");
  }
  if (!shapes.length) {
    lines.push("ink: none: nothing is painted");
    if (unread.length) lines.push(`not read: ${unread.join(", ")}`);
    return lines.join("\n");
  }
  const all = union(shapes.map((s) => s.box));
  const small = shapes.filter((s) => s.box.w < SMALL * all.w && s.box.h < SMALL * all.h);
  const listed = shapes.filter((s) => !small.includes(s));
  /* the ink is the listed shapes' box: a speck at the corner does not stretch it */
  const ink = union((listed.length ? listed : shapes).map((s) => s.box));
  lines.push(`ink: ${span(ink)}  (${Math.round((ink.w / vw) * 100)}% × ${Math.round((ink.h / vh) * 100)}% of the viewBox)${dark ? "  light ink: the picture is on dark" : ""}`, "");
  const rel = relate(listed, ink);
  const shown = listed.slice(0, LISTED);
  shown.forEach((s, k) => {
    const [cx, cy] = centre(s.box);
    const paint = [s.filled && "filled", s.stroke !== null && `stroke ${r1(s.stroke)}`].filter(Boolean).join(", ") || "no paint";
    const shape = [s.closed ? "closed" : "open", s.kind, s.part && `part ${s.part}`].filter(Boolean).join(", ");
    const tall = s.box.h > s.box.w * 1.5 ? `  (tall, ${ratio(s.box.w, s.box.h)})` : s.box.w > s.box.h * 1.5 ? `  (wide, ${ratio(s.box.w, s.box.h)})` : "";
    const note = rel[k] ? `  ${rel[k]}` : tall;
    lines.push(`#${pad(s.i, 2)} ${pad(s.type, 7)} ${pad(s.group ? `g#${s.group}` : "-", 9)} box ${span(s.box)}  centre ${r1(cx)},${r1(cy)}  ${paint}  ${shape}${note}`);
  });
  if (listed.length > shown.length) lines.push(`and ${listed.length - shown.length} more shapes`);
  if (small.length) lines.push(`and ${plural(small.length, "small shape")}`);
  if (unread.length) lines.push(`not read: ${unread.join(", ")}`);
  return lines.slice(0, 30).join("\n");
}

/** The page the picture is taken of: the SVG at 400 × 400 on white, or on dark, kept whole inside the box. */
export function page(xml, viewBox, dark = false) {
  const svg = xml.replace(/<\?xml[\s\S]*?\?>|<!DOCTYPE[^[>]*(?:\[[\s\S]*?\])?\s*>/gi, "").replace(/<svg\b([^>]*)>/, (m, attrs) => {
    const kept = attrs.replace(/\s(width|height|viewBox|preserveAspectRatio)\s*=\s*(?:"[^"]*"|'[^']*')/g, "");
    return `<svg${kept} viewBox="${viewBox.join(" ")}" width="400" height="400" preserveAspectRatio="xMidYMid meet">`;
  });
  return `<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:${dark ? "#18181b" : "#fff"}}#box{width:400px;height:400px;color:#18181b}#box>svg{display:block}</style><div id="box">${svg}</div>`;
}

/* Measured in the page: every painted shape in paint order, its box in the root's viewBox units with every transform applied, and its colour. A <use> that points inside the file is one shape, by what it draws; a path drawn in several pieces is one shape per piece. */
const MEASURE = () => {
  const root = document.querySelector("#box > svg");
  /* screen CTMs, not getCTM(): getCTM() stops at the nearest viewport, which inside a nested <svg> is not the root */
  const toRoot = root.getScreenCTM().inverse();
  const hidden = "defs, symbol, clipPath, mask, pattern, marker";
  const els = [...root.querySelectorAll("path, rect, circle, ellipse, line, polyline, polygon, use")].filter((el) => !el.parentElement.closest(hidden));
  const list = [];
  const NUM = "([+-]?(?:\\d+\\.?\\d*|\\.\\d+)(?:e[+-]?\\d+)?)";
  const START = new RegExp(`^\\s*[Mm]\\s*${NUM}[\\s,]*${NUM}`, "i");
  /* The pieces of a path, each from its own move: each measured alone, a relative move taken from where the piece before it ended. Null for one piece. */
  const pieces = (el) => {
    const all = (el.getAttribute("d") ?? "").split(/(?=[Mm])/).filter((p) => /\S/.test(p));
    if (all.length < 2) return null;
    const tmp = document.createElementNS(el.namespaceURI, "path");
    el.parentNode.insertBefore(tmp, el);
    try {
      const out = [];
      let at = [0, 0];
      for (const piece of all) {
        const m = START.exec(piece);
        if (!m) return null;
        const rel = piece.trimStart()[0] === "m";
        const from = rel ? [at[0] + Number(m[1]), at[1] + Number(m[2])] : [Number(m[1]), Number(m[2])];
        const rest = piece.slice(m[0].length);
        /* pairs right after a move are lines, relative after m */
        tmp.setAttribute("d", `M${from[0]} ${from[1]}${/^[\s,]*[-+.\d]/.test(rest) ? (rel ? " l" : " L") : ""}${rest}`);
        const length = tmp.getTotalLength();
        const end = length > 0 ? tmp.getPointAtLength(length) : null;
        at = end ? [end.x, end.y] : from;
        const b = tmp.getBBox();
        if (b.width > 0 || b.height > 0) out.push({ b, d: piece });
      }
      return out.length > 1 ? out : null;
    } finally {
      tmp.remove();
    }
  };
  const boxIn = (b, m) => {
    const pts = [[b.x, b.y], [b.x + b.width, b.y], [b.x, b.y + b.height], [b.x + b.width, b.y + b.height]].map(([x, y]) => new DOMPoint(x, y).matrixTransform(m));
    const xs = pts.map((p) => p.x), ys = pts.map((p) => p.y);
    const x = Math.min(...xs), y = Math.min(...ys);
    return { x, y, w: Math.max(...xs) - x, h: Math.max(...ys) - y };
  };
  for (const el of els) {
    if (el.tagName === "use" && !(el.getAttribute("href") ?? el.getAttribute("xlink:href") ?? "").startsWith("#")) continue;
    let b;
    try { b = el.getBBox(); } catch { continue; }
    if (!(b.width > 0 || b.height > 0)) continue;
    const m = toRoot.multiply(el.getScreenCTM());
    const cs = getComputedStyle(el);
    const tag = el.tagName;
    const curvesOf = (d) => [/[CcSsQqTtAa]/.test(d) && "curves", /[LlHhVv]/.test(d) && "lines"].filter(Boolean).join(" and ");
    const kind = ["circle", "ellipse"].includes(tag) ? "curves"
      : tag === "rect" && Number(el.getAttribute("rx") || el.getAttribute("ry") || 0) > 0 ? "curves and lines"
      : tag === "use" ? "" : "lines";
    const sw = parseFloat(cs.strokeWidth);
    const filled = cs.fill !== "none" && parseFloat(cs.fillOpacity) !== 0;
    const stroke = cs.stroke !== "none" && sw > 0 ? sw : null;
    const common = { type: tag, group: el.parentElement.closest("g[id]")?.id ?? null, filled, stroke, colour: filled ? cs.fill : stroke !== null ? cs.stroke : null };
    const parts = tag === "path" ? pieces(el) : null;
    if (parts) {
      parts.forEach((p, k) => list.push({ i: list.length + 1, ...common, box: boxIn(p.b, m), closed: /[Zz]/.test(p.d), kind: curvesOf(p.d), part: `${k + 1} of ${parts.length}` }));
      continue;
    }
    const d = el.getAttribute("d") ?? "";
    const closed = tag === "path" ? /[Zz]/.test(d) : !["line", "polyline"].includes(tag);
    list.push({ i: list.length + 1, ...common, box: boxIn(b, m), closed, kind: tag === "path" ? curvesOf(d) : kind });
  }
  return list;
};

/** The picture, the shapes and whether the picture is on dark, from a fresh context of a browser the caller owns. The SVG's scripts never run and nothing is fetched: a file from anywhere is drawn as written. */
export async function snapshot(browser, xml, viewBox) {
  const context = await browser.newContext({ viewport: { width: 400, height: 400 }, deviceScaleFactor: 2, colorScheme: "light", javaScriptEnabled: false, offline: true });
  try {
    const p = await context.newPage();
    await p.setContent(page(xml, viewBox));
    const shapes = await p.evaluate(MEASURE);
    const dark = light(shapes);
    if (dark) await p.setContent(page(xml, viewBox, true));
    const png = (await p.screenshot({ clip: { x: 0, y: 0, width: 400, height: 400 } })).toString("base64");
    return { png, shapes, dark };
  } finally {
    await context.close();
  }
}

/** The reading of one SVG. Prints as it goes and returns the exit code. */
export async function read(src, given = {}, cwd = process.cwd()) {
  let xml;
  try { xml = readFileSync(src, "utf8"); } catch { console.error(`read: cannot read ${resolve(src)}`); return 2; }
  const info = scan(xml, basename(src));
  if (info.error) { console.error(`read: ${info.error}`); return 2; }
  const name = nameFor(src, given.name ?? null);
  const txt = join(cwd, `hairline-${name}-source.txt`), png = join(cwd, `hairline-${name}-source.png`);

  const { cacheDir, launch, playwright } = await import("./look.mjs");
  let browser = null, why = "";
  try { browser = await launch(playwright(cacheDir())); } catch (e) { why = e.message.split("\n")[0]; }
  let text;
  if (!browser) {
    text = card(info);
    console.log(`no browser: ${why || "neither Chrome nor Playwright's Chromium would start"}. The card is reduced to what the XML says, and no picture was taken.`);
  } else {
    try {
      const { png: b64, shapes, dark } = await snapshot(browser, xml, info.viewBox);
      writeFileSync(png, Buffer.from(b64, "base64"));
      text = card(info, shapes, dark);
      console.log(`picture ${png}`);
    } catch (e) {
      /* the browser started but could not draw this file: the reduced card is still a reading */
      text = card(info);
      console.log(`no picture: the browser could not draw it: ${e.message.split("\n")[0]}. The card is reduced to what the XML says.`);
    } finally {
      await browser.close();
    }
  }
  writeFileSync(txt, text + "\n");
  console.log(`card ${txt}`);
  console.log(text);
  return 0;
}

/* The skill is often installed as a symlink, so the path Node was given is resolved before it is compared. */
if (process.argv[1] && same(realpathSync(process.argv[1]), realpathSync(here("./read.mjs")))) {
  let args;
  try {
    args = parseArgs({ allowPositionals: true, options: { name: { type: "string" } } });
  } catch (e) {
    console.error(`${e.message}\n${USAGE}`);
    process.exit(2);
  }
  const { positionals: [src], values } = args;
  if (!src) { console.error(USAGE); process.exit(2); }
  process.exit(await read(src, { name: values.name ?? null }));
}

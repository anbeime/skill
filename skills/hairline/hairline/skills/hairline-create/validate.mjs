#!/usr/bin/env node
/**
 * Checks a page made by build.mjs: `node validate.mjs hairline-<name>.html`.
 * It prints what to fix and exits 1, or prints `ok` and exits 0. The checks
 * read the text of the file, so they catch what is mechanical; the look
 * (look.md) catches the rest. Each line it prints starts with the check's name:
 *
 *   kernel    the kernel in the page is this folder's kernel.js, untouched
 *   parse     the figure loads as a module: no syntax error stops it before it draws
 *   bench     nothing but the figure differs from bench.html
 *   text      no words inside the figure (rule 10)
 *   paint     no stroke width, colour, fill, opacity, filter or shadow of its own (rule 04)
 *   outside   nothing loaded or reached outside the file; every node from HL.mk
 *   clock     no timers, frames or SMIL animation of its own; it joins HL.register (rule 07)
 *   tween     every tset is given its four values, the delay last
 *   hit       input only through HL.pointer; nothing measured on screen (rule 01)
 *   readout   it writes read.textContent
 *   handle    mount returns { set, destroy }
 *   declare   the file ends with hairline({ name, means, rules, range, tour, mount })
 *   tour      hairline() gives tour: three to six stops, each [x, y] in the viewBox or null, one of them a point; the figure never calls HL.tour
 *   length    at most 200 lines
 */
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtempSync, readFileSync, realpathSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { assemble } from "./build.mjs";

const here = (p) => fileURLToPath(new URL(p, import.meta.url));
const LIMIT = 200;
const unix = (s) => s.replace(/\r\n/g, "\n");
/**
 * A figure's source without its comments, so its prose is never read as code.
 * It is read the way JavaScript reads it, so a `//` inside a string, a template
 * or a regex is not taken for a comment, and what follows it is still checked.
 * With `words` false the strings are emptied too, for a check that must not
 * read a string's words as code.
 */
function bare(src, words = true) {
  let out = "", i = 0, prev = "", depth = 0;
  const open = []; // for each `${` still open, the brace depth it opened at
  /** Reads from just past an opening quote to its close, or, in a template, to a `${`. */
  const quoted = (q) => {
    const from = i;
    while (i < src.length && src[i] !== q && (q === "`" ? !(src[i] === "$" && src[i + 1] === "{") : src[i] !== "\n")) {
      i += src[i] === "\\" ? 2 : 1;
    }
    if (words) out += src.slice(from, i);
    if (q === "`" && src[i] === "$") { out += "${"; i += 2; open.push(depth++); prev = "{"; return; }
    out += src[i] ?? ""; i++; prev = q;
  };
  while (i < src.length) {
    const c = src[i], d = src[i + 1];
    if (c === "/" && d === "/") { while (i < src.length && src[i] !== "\n") i++; }
    else if (c === "/" && d === "*") { const end = src.indexOf("*/", i + 2); i = end < 0 ? src.length : end + 2; out += " "; }
    else if (c === "/" && /^(?:|[(,=:[!&|?{};+\-*%<>~^])$/.test(prev)) {
      // A regex: a slash where a value starts. A quote or a `//` inside it is the regex's own.
      let j = i + 1, cls = false;
      for (; j < src.length && src[j] !== "\n"; j++) {
        if (src[j] === "\\") j++;
        else if (src[j] === "[") cls = true;
        else if (src[j] === "]") cls = false;
        else if (src[j] === "/" && !cls) break;
      }
      out += src.slice(i, j + 1); i = j + 1; prev = ")";
    } else if (c === '"' || c === "'" || c === "`") { out += c; i++; quoted(c); }
    else if (c === "}" && open.length && depth - 1 === open[open.length - 1]) { depth--; open.pop(); out += c; i++; quoted("`"); }
    else {
      if (c === "{") depth++;
      else if (c === "}") depth--;
      out += c; i++;
      if (!/\s/.test(c)) prev = c;
    }
  }
  return out;
}

/**
 * What a figure must not contain: a pattern read in the code with its strings,
 * and, for an import, one read with its strings emptied, so the word in a
 * string is not taken for the statement.
 */
const BAD = [
  ["text", /<\s*(?:text|tspan|textPath|foreignObject)\b|["'`](?:text|tspan|textPath|foreignObject)["'`]|\b(?:innerHTML|outerHTML|insertAdjacentHTML|innerText)\b/,
    "rule 10. No words inside the figure, and no markup written as a string. Say it with geometry (a punch, a dot code, a bright edge); names go to read.textContent."],
  ["paint", /stroke-width|strokeWidth|stroke-dasharray|-opacity|(?:fill|stroke)Opacity|["'`](?:fill|stroke|filter|style|color|stop-color|opacity)["'`]|\b(?:fill|stroke|filter|style|opacity)\s*:|\.style\b|(["'`])#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\1|\b(?:rgba?|hsla?|oklch|oklab|color-mix)\(|drop-shadow|box-shadow|feDropShadow|feGaussianBlur|[Ll]inearGradient|[Rr]adialGradient|(?:linear|radial|conic)-gradient/,
    "rule 04. The figure sets a stroke width, colour, fill, opacity, filter, gradient or shadow of its own. Use the kernel's classes and nothing else: sil, hi, lo, nf, fo, dash, dot, dot m, dot off."],
  ["outside", /\bfetch\s*\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon|https?:\/\/|\burl\(|<\/?script|<(?:link|img|iframe|style)\b|new\s+Image\b|createElement|\beval\s*\(|new\s+Function\b|localStorage|sessionStorage|\.cookie\b/,
    "the figure reaches outside the file or makes nodes by hand. One self-contained file: no fetch, import, URL, script tag or storage, and every node comes from HL.mk.",
    // The keyword ends where the binding starts, so `important` or `imported` is a name, not an import.
    // `import.meta` is left alone on purpose: by itself it reaches nothing outside the file.
    /\bimport(?:\s*["'`({*]|\s+[\w$]+\s*(?:,|from\b))/],
  ["clock", /\bsetInterval\b|\bsetTimeout\b|\brequestAnimationFrame\b|\.animate\s*\(|<animate|["'`]animate(?:Transform|Motion)?["'`]|IntersectionObserver|\bmatchMedia\b/,
    "rule 07. The figure runs a clock of its own. Move inside HL.register(stage, tick), with springs (stepS) or tweens (tset, tval); a delay is a tween's delay. The loop sleeps offscreen and honours reduced motion for you."],
  ["hit", /getBoundingClientRect|elementFromPoint|elementsFromPoint|:hover|(?:addEventListener|\.on)\s*\(\s*(?:\w+\s*,\s*)?["'`](?:mouse|pointer|touch|click)|\bon(?:mouse|pointer|touch|click)\w*\s*=/,
    "rule 01. The figure listens to the pointer itself or measures what is on screen. Take the pointer from HL.pointer(stage, { move, leave }) and test it against the rest or target pose, in world units."],
];

/**
 * What a figure must contain. The handle's keys may be written `set(v)`, `set: f`
 * or, shorthand, `{ set, destroy }`. A call on something else, such as
 * `map.set(k, v)`, is not the handle's `set`.
 */
const NEED = [
  ["clock", /\bregister\s*\(/, "rule 07. The figure never joins the kernel's loop. Draw inside HL.register(stage, tick), and give its unregister to destroy."],
  ["hit", /\bpointer\s*\(/, "the figure never listens to the pointer. Call HL.pointer(stage, { move, leave }) and answer it."],
  ["readout", /\bread\.textContent\s*=/, 'the figure never writes the read-out. Set read.textContent to what is under the pointer, and to "rest" when nothing is.'],
  ["handle", /(?<![.\w$])set\s*[:(,}]/, "mount must return { set(value), destroy() }, and set is missing. It takes the slider's number."],
  ["handle", /(?<![.\w$])destroy\s*[:(,}]/, "mount must return { set(value), destroy() }, and destroy is missing. It undoes everything mount did: bag.dispose."],
];

/**
 * Each `tset` given fewer than its four values. Without its delay a tween
 * starts at no time at all: its value is NaN, and so is every path drawn from it.
 */
function tweens(shape) {
  const out = [];
  for (const m of shape.matchAll(/(?<![\w$])tset\s*\(/g)) {
    let i = m.index + m[0].length, depth = 1, given = 1;
    for (; i < shape.length && depth; i++) {
      const c = shape[i];
      if ("([{".includes(c)) depth++;
      else if (")]}".includes(c)) depth--;
      else if (c === "," && depth === 1) given++;
    }
    const call = shape.slice(m.index, i).replace(/\s+/g, " ");
    if (given < 4 && !call.includes("...")) {
      out.push(`tween: \`${call}\` is given ${given} of tset's four values: tset(tw, to, now, delay). Without the delay the tween's value is NaN and nothing is drawn. Give it 0 to start at once.`);
    }
  }
  return out;
}

/** The declaration at the end of the file, read as text. */
function declared(code) {
  const say = (what) => `declare: the file must end with hairline({ name, means, rules, range, tour, mount }). ${what}`;
  const m = /\bhairline\s*\(\s*\{([\s\S]*?)\}\s*\)\s*;?\s*$/.exec(code.trimEnd());
  if (!m) return [say("That call is missing, or is not the last statement.")];
  const d = m[1], wrong = [];
  const list = (key) => {
    const a = new RegExp(`\\b${key}:\\s*\\[([^\\]]*)\\]`).exec(d);
    return a ? a[1].split(",").map((s) => s.trim()).filter(Boolean).map(Number) : null;
  };
  if (!/\bname:\s*(["'`])[a-z][a-z0-9-]{1,30}\1/.test(d)) wrong.push("name (lowercase letters, digits and hyphens)");
  if (!/\bmeans:\s*(["'`])(?:(?!\1).){1,140}\1/.test(d)) wrong.push("means (one sentence, at most 140 characters)");
  const rules = list("rules"), range = list("range");
  if (!rules || !rules.length || rules.some((r) => !Number.isInteger(r) || r < 1 || r > 10)) wrong.push("rules (the numbers, 1 to 10, of the rules it leans on)");
  const oneWay = range && range.length === 3 && range.every(Number.isFinite) && range[0] !== range[2] && (range[1] - range[0]) * (range[2] - range[1]) >= 0;
  if (!oneWay) wrong.push("range (three numbers that move one way: the figure's value at intensity 0, 0.5 and 1)");
  if (!/\bmount\b/.test(d)) wrong.push("mount");
  return wrong.length ? [say(`Wrong or missing: ${wrong.join("; ")}.`)] : [];
}

/**
 * The tour: three to six stops in the hairline() call, each a literal [x, y]
 * inside the viewBox or null, at least one a point. The figure's own code never
 * calls HL.tour; the bench and the package do.
 */
function toured(code, shape) {
  const out = [];
  if (/\bHL\.tour\s*\(/.test(shape)) out.push("tour: the figure calls HL.tour itself. Declare tour in hairline() and let the bench play it.");
  const call = /\bhairline\s*\(\s*\{([\s\S]*?)\}\s*\)\s*;?\s*$/.exec(code);
  if (!call) return out;                                   // declare already said so
  const body = call[1];
  const open = /\btour:\s*\[/.exec(body);
  if (!open) { out.push("tour: the call gives no tour. Add tour: [[x, y], ..., null], three to six stops that walk the figure through its answer."); return out; }
  let depth = 0, end = -1;
  for (let i = open.index + open[0].length - 1; i < body.length; i++) {
    if (body[i] === "[") depth++;
    else if (body[i] === "]" && --depth === 0) { end = i; break; }
  }
  if (end < 0) { out.push("tour: the tour's brackets do not close."); return out; }
  const inner = body.slice(open.index + open[0].length, end);
  const items = inner.match(/\[\s*([^\[\]]*)\]|null|[^\s,\[\]]+/g) ?? [];
  const bad = [];
  let points = 0;
  for (const item of items) {
    if (item === "null") continue;
    const m = /^\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]$/.exec(item);
    const x = m && Number(m[1]), y = m && Number(m[2]);
    if (!m || x < 0 || x > 400 || y < 0 || y > 320) { bad.push(item.replace(/\s+/g, " ")); continue; }
    points++;
  }
  if (bad.length) out.push(`tour: each stop is a literal [x, y] with x in 0..400 and y in 0..320, or null. Not: ${bad.join(", ")}.`);
  if (items.length < 3 || items.length > 6) out.push(`tour: ${items.length} stop${items.length === 1 ? "" : "s"}. A tour has three to six: enough to show the answer, few enough to stay a sentence.`);
  if (!bad.length && !points) out.push("tour: every stop is null. At least one stop is a point on the figure.");
  return out;
}

/**
 * The syntax error that keeps the figure from loading, or nothing. The page
 * loads the figure as a module, so it is checked as one, by `node --check`:
 * the browser would stop at the same error and draw nothing.
 */
function parse(src) {
  const dir = mkdtempSync(join(tmpdir(), "hl-parse-")), file = join(dir, "figure.mjs");
  try {
    writeFileSync(file, src);
    const run = spawnSync(process.execPath, ["--check", file], { encoding: "utf8" });
    if (run.status === 0) return [];
    const line = /figure\.mjs:(\d+)/.exec(run.stderr)?.[1];
    const error = /^\w*Error: .*$/m.exec(run.stderr)?.[0] ?? run.stderr.trim().split("\n")[0];
    return [`parse: the figure does not load${line ? `, line ${line}` : ""}: ${error}. The browser stops there and draws nothing. Fix it in the figure and build again.`];
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

/** Everything wrong with a page, one line each; empty when it passes. */
export function validate(input) {
  const page = unix(input), out = [];

  const kernel = unix(readFileSync(here("./kernel.js"), "utf8")).trimEnd();
  const cut = kernel.indexOf("\n");
  const hash = /sha256:([0-9a-f]{64})/.exec(kernel.slice(0, cut))?.[1];
  if (hash !== createHash("sha256").update(kernel.slice(cut + 1) + "\n").digest("hex")) {
    out.push("kernel: kernel.js in the skill folder has been edited. Install the skill again; the kernel is never changed by hand.");
  }

  const fig = /<script type="module" id="hl-figure">\n([\s\S]*?)\n<\/script>/.exec(page);
  if (!fig) return [...out, "bench: the page has no figure slot. Make it with `node build.mjs <figure.js>`, not by hand."];
  if (!page.includes(kernel)) {
    out.push("kernel: the kernel in the page is not kernel.js. Build again with `node build.mjs`; never edit or retype the kernel.");
  } else if (page.trimEnd() !== assemble(fig[1]).trimEnd()) {
    out.push("bench: the page differs from bench.html outside the figure. Build again with `node build.mjs`; the bench is fixed, and a change belongs in the figure.");
  }

  const src = fig[1], code = bare(src), shape = bare(src, false);
  out.push(...parse(src));
  for (const [id, re, say, empty] of BAD) if (re.test(code) || empty?.test(shape)) out.push(`${id}: ${say}`);
  for (const [id, re, say] of NEED) if (!re.test(code)) out.push(`${id}: ${say}`);
  out.push(...tweens(shape));
  out.push(...declared(code));
  out.push(...toured(code, shape));
  const lines = src.split("\n").length;
  if (lines > LIMIT) out.push(`length: the figure is ${lines} lines and the limit is ${LIMIT}. A figure this long is usually two ideas: cut the concept down to one.`);
  return out;
}

/** Whether two resolved paths are one file. Windows paths ignore case, and the drive letter's case can differ between the two. */
export const same = (a, b, platform = process.platform) => platform === "win32" ? a.toLowerCase() === b.toLowerCase() : a === b;

/* The skill is often installed as a symlink, so the path Node was given is resolved before it is compared. */
if (process.argv[1] && same(realpathSync(process.argv[1]), realpathSync(here("./validate.mjs")))) {
  const file = process.argv[2];
  if (!file) {
    console.error("usage: node validate.mjs <page.html>");
    process.exit(2);
  }
  let page;
  try { page = readFileSync(file, "utf8"); } catch {
    console.error(`cannot read ${file}`);
    process.exit(2);
  }
  const problems = validate(page);
  if (problems.length) {
    for (const p of problems) console.error(p);
    console.error(`${problems.length} to fix in ${file}`);
    process.exit(1);
  }
  console.log(`ok ${file}: kernel and bench intact, and the figure passes the static checks. Now the look: look.md.`);
}

#!/usr/bin/env node
/**
 * The look in one command, run from the person's working directory:
 *
 *   node <skill folder>/look.mjs <name>.js --answer x,y,z [--edge x,y,z [--edge x,y,z]] [--zoom <shot>] [--source <file.svg>]
 *
 * It builds and validates the page as build.mjs and validate.mjs do, opens
 * look.md's eight addresses at once in one browser, and writes the eight
 * pictures, labelled, on one sheet: hairline-<name>-look.png. Beside it go the
 * two 240px pictures with the name and the read-out hidden, for a reader told
 * nothing, hairline-<name>-blind.png, and, when there is an answer point, the
 * stage taken while the answer plays, rest to answer, hairline-<name>-motion.png.
 * Then it prints what can be measured, one line each, under look.md's item
 * numbers: 9 the frame, 8 the read-out, 12 the console, 4 the flicker, and 3
 * how much of the thumbnail's ink the pointer moves. It exits 1 when the
 * validator rejects the page or one of those fails, 2 when it cannot run, and
 * 0 otherwise. Everything else is for eyes, on the three pictures.
 *
 * A point is a world point x,y,z, run through the P the figure made with its
 * own camera, or a viewBox point x,y, taken as it is. --answer is on the part
 * that should answer the pointer. --edge is at the figure's edge, for the two
 * ends of the slider; given twice, the first is for intensity 0 and the second
 * for 1. Without them, an `answer` or `edge` the figure gives in its
 * hairline({ … }) call is used. --zoom writes one shot's stage at three times
 * the pixels.
 *
 * The browser is Playwright's. playwright-core is installed once into a cache
 * folder of the user's (HAIRLINE_LOOK_CACHE moves it), never into the skill or
 * the working directory, and it drives the installed Chrome, or Playwright's
 * own Chromium when there is no Chrome.
 */
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { homedir } from "node:os";
import { basename, dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { parseArgs } from "node:util";
import { assemble, nameOf } from "./build.mjs";
import { validate } from "./validate.mjs";

const here = (p) => fileURLToPath(new URL(p, import.meta.url));
const USAGE = "usage: node look.mjs <name>.js --answer x,y,z [--edge x,y,z [--edge x,y,z]] [--zoom <shot>] [--source <file.svg>]";
/** Each picture waits 1.5 seconds after its page loads, then until its drawing holds still for a quarter of a second, and no longer than 5 seconds from the load. */
const WAIT = 1500, STILL = 250, CAP = 5000;
/** A rest pose whose box covers less of the frame than this is reported as small. Both examples' rest boxes cover 36%: Terrain's 297 × 155, Riffle's 226 × 205. */
const SMALL = 0.25;
/** An answer that moves less of the thumbnail's ink than this is reported as faint. Terrain's answer moves 74%, Riffle's 139%; this is half the smaller. */
const FAINT = 0.37;
/** A pixel this far from the ground on any channel is ink: the dim stroke on a white plate stands 31 from it. */
const INKED = 24;
/** The motion strip: 16 frames of the stage 40ms apart, four to a row. The last, at 600ms, is most of the way through a 700ms tween; the sheet's answer picture is where it ends. */
const FRAMES = 16, EVERY = 40, ACROSS = 4;

/** The share of the rest picture's ink the answer moved: pixels inked in one and not the other, over the rest's ink. Each mask is a row of 0s and 1s. */
export function moved(rest, answer) {
  let ink = 0, changed = 0;
  for (let i = 0; i < rest.length; i++) { ink += rest[i]; if (rest[i] !== answer[i]) changed++; }
  return ink ? changed / ink : 0;
}

/** When each frame of the motion strip is taken, in ms after the pointer arrives: the first at rest, as it arrives, the others every `every` ms after. */
export function beats(n = FRAMES, every = EVERY) {
  return Array.from({ length: n }, (_, i) => i * every);
}

/* A picture's ink, read in the page: 1 where a pixel stands INKED or more from the ground, the colour 14px inside the picture's top left corner, on the plate and clear of the drawing. The outer 12px, where the plate's own outline runs, are left out. */
const INK = async ([b64, INKED]) => {
  const img = new Image();
  img.src = "data:image/png;base64," + b64;
  await img.decode();
  const c = Object.assign(document.createElement("canvas"), { width: img.width, height: img.height }), x = c.getContext("2d");
  x.drawImage(img, 0, 0);
  const d = x.getImageData(0, 0, c.width, c.height).data, at = (px, py) => 4 * (py * c.width + px), g = at(14, 14), mask = [];
  for (let py = 12; py < c.height - 12; py++) for (let px = 12; px < c.width - 12; px++) {
    const i = at(px, py);
    mask.push(Math.max(Math.abs(d[i] - d[g]), Math.abs(d[i + 1] - d[g + 1]), Math.abs(d[i + 2] - d[g + 2])) >= INKED ? 1 : 0);
  }
  return mask;
};

/** look.md's eight pictures, in its order: the shot's name, what it adds to the address, and which point it holds. */
export const SHOTS = [
  ["rest", "", null],
  ["answer", "", "answer"],
  ["small", "w=240", null],
  ["small-answer", "w=240", "answer"],
  ["low", "intensity=0", "low"],
  ["high", "intensity=1", "high"],
  ["dark", "theme=dark", "answer"],
  ["light", "theme=light", "answer"],
];

/** The folder playwright-core is installed into: the user's cache folder, or HAIRLINE_LOOK_CACHE. */
export function cacheDir(env = process.env, platform = process.platform, home = homedir()) {
  if (env.HAIRLINE_LOOK_CACHE) return resolve(env.HAIRLINE_LOOK_CACHE);
  if (platform === "darwin") return join(home, "Library", "Caches", "hairline-look");
  if (platform === "win32") return join(env.LOCALAPPDATA || join(home, "AppData", "Local"), "hairline-look");
  return join(env.XDG_CACHE_HOME || join(home, ".cache"), "hairline-look");
}

/** A point given on the command line: three numbers for the world, two for the viewBox, or null. */
export function point(s) {
  const n = String(s ?? "").split(",").map((v) => (v.trim() === "" ? NaN : Number(v)));
  return (n.length === 2 || n.length === 3) && n.every(Number.isFinite) ? n : null;
}

/** playwright-core from the cache, installed there first when it is not. Throws with a reason when it cannot be had. */
export function playwright(dir) {
  const req = createRequire(join(dir, "look.cjs"));
  const has = () => { try { return req.resolve("playwright-core/package.json"); } catch { return null; } };
  if (!has()) {
    console.log(`installing playwright-core once, into ${dir}`);
    mkdirSync(dir, { recursive: true });
    try { writeFileSync(join(dir, "package.json"), '{ "private": true }\n', { flag: "wx" }); } catch { /* already there */ }
    const win = process.platform === "win32";
    const run = spawnSync(win ? "npm.cmd" : "npm", ["install", "playwright-core@1", "--prefix", dir, "--no-audit", "--no-fund", "--loglevel=error"], { encoding: "utf8", shell: win });
    const why = run.error?.code === "ENOENT" ? "npm is not on the PATH" : run.error?.message ?? /Error: (.*)$/m.exec(run.stderr)?.[1] ?? run.stderr.trim().split("\n")[0];
    if (run.status !== 0 || !has()) throw new Error(why || "npm failed");
  }
  return { chromium: req("playwright-core").chromium, cli: join(dirname(has()), "cli.js") };
}

/** Starts the browser: the installed Chrome, or Playwright's own Chromium when there is none. Rejects when neither launches. */
export function launch(pw) {
  return pw.chromium.launch({ channel: "chrome" }).catch(() => pw.chromium.launch());
}

/*
 * Keeps the P the figure makes from its own camera, so a world point can be
 * turned into an ?at= point, and the `answer` and `edge` points a figure may
 * give in its hairline({ … }) call. The bench is not touched: both are caught
 * as the page sets them.
 */
const TRAP = () => {
  let hl, call;
  Object.defineProperty(window, "HL", { configurable: true, get: () => hl, set: (v) => { hl = { ...v, proj: (C) => (window.P = v.proj(C)) }; } });
  Object.defineProperty(window, "hairline", {
    configurable: true,
    get: () => call,
    set: (v) => {
      call = (figure) => {
        window.declared = { answer: figure.answer ?? null, edge: figure.edge ?? null };
        return v(figure);
      };
    },
  });
};

/**
 * What the page shows after the wait: the drawing's box in viewBox units, the
 * read-out, the line under the stage, and the part of the page a picture
 * keeps, from the plate's top to the last line under it. The box is getBBox's,
 * so it is geometry: a stroke reaches half its width past it.
 */
const STATE = () => {
  const $ = (s) => document.querySelector(s), svg = $("#stage > svg"), err = $("#error");
  const b = svg && svg.childElementCount ? svg.getBBox() : null;
  const plate = $(".plate").getBoundingClientRect();
  const bottom = Math.max(...["#means", "#error"].map((s) => $(s)).filter((el) => !el.hidden).map((el) => el.getBoundingClientRect().bottom));
  return {
    box: b && { x: b.x, y: b.y, w: b.width, h: b.height },
    read: $("#read").textContent,
    error: err.hidden ? "" : err.textContent,
    clip: { x: Math.max(0, plate.left - 8), y: Math.max(0, plate.top - 8), width: plate.width + 16, height: bottom - plate.top + 16 },
    stage: { x: plate.left, y: plate.top, width: plate.width, height: plate.height },
  };
};

/* The pointer at a viewBox point x,y, put there as the bench's ?at= puts it: one pointermove on the stage. */
const POINT = (at) => {
  const [x, y] = at.split(",").map(Number), stage = document.getElementById("stage"), r = stage.getBoundingClientRect();
  stage.dispatchEvent(new PointerEvent("pointermove", {
    pointerType: "mouse", pointerId: 1, bubbles: true,
    clientX: r.left + (x / 400) * r.width, clientY: r.top + (y / 320) * r.height,
  }));
};

/** A browser context with look.md's window: 800 × 900, so ?w=240 narrows the page and not the window. */
const window800 = (browser, scale = 1) => browser.newContext({ viewport: { width: 800, height: 900 }, deviceScaleFactor: scale, colorScheme: "light" });
const sleep = (ms) => new Promise((done) => setTimeout(done, ms));
const drawing = (page) => page.evaluate(() => document.querySelector("#stage > svg")?.innerHTML ?? "");

/** Waits out the settle, then until the drawing holds still. Returns the seconds from the load to the still drawing, or null when it never held still. */
async function settle({ page, loaded }) {
  await sleep(loaded + WAIT - Date.now());
  for (let was = await drawing(page); Date.now() + STILL - loaded <= CAP;) {
    await sleep(STILL);
    const now = await drawing(page);
    if (now === was) return (Date.now() - loaded) / 1000;
    was = now;
  }
  return null;
}

/**
 * Opens a page and collects what it says on the console. The pages of one
 * context are each laid out in a viewport of their own, so every figure's
 * IntersectionObserver finds it on screen and its loop runs.
 */
async function open(context, url, trap = false) {
  const page = await context.newPage(), bad = [];
  page.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") bad.push(`console ${m.type()}: ${m.text()}`); });
  page.on("pageerror", (e) => bad.push(`page error: ${e.message}`));
  if (trap) await page.addInitScript(TRAP);
  await page.goto(url);
  return { page, bad, loaded: Date.now() };
}

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => `&#${c.charCodeAt(0)};`);
/** The sheet: rest and answering large, the two thumbnails at their own size beside the themes, then the slider's two ends. With a source, a first row puts the drawing beside rest at the same size. */
function sheet(name, shots, source = null) {
  const cell = (s, cls = "") => `<figure class="${cls}"><figcaption>${esc(s.label)}</figcaption><img src="data:image/png;base64,${s.png}"></figure>`;
  const by = Object.fromEntries(shots.map((s) => [s.name, s]));
  return `<!doctype html><meta charset="utf-8"><style>
  body { margin: 0; padding: 16px; width: 1400px; box-sizing: border-box; background: #ececef; color: #18181b; font: 13px/1.3 ui-monospace, Menlo, Consolas, monospace; }
  h1 { font: inherit; margin: 0 0 10px; color: #55555c; }
  .row { display: flex; gap: 16px; align-items: flex-start; margin-bottom: 16px; }
  figure { margin: 0; flex: 1 1 0; min-width: 0; }
  figure.own { flex: 0 0 272px; }
  figcaption { margin: 0 0 6px; overflow-wrap: anywhere; }
  img { display: block; width: 100%; outline: 1px solid #c9c9ce; }
  .own img { width: auto; }
</style><h1>hairline-${esc(name)} · the look</h1>
${source ? `<div class="row">${cell({ label: `source  ${source.file}`, png: source.png })}${cell({ label: "rest", png: by.rest.png })}</div>` : ""}
<div class="row">${cell(by.rest)}${cell(by.answer)}</div>
<div class="row">${cell(by.small, "own")}${cell(by["small-answer"], "own")}${cell(by.dark)}${cell(by.light)}</div>
<div class="row">${cell(by.low)}${cell(by.high)}</div>`;
}

/** The motion strip: the stage's frames, ACROSS to a row at their own size, each under its time since the pointer arrived. */
function strip(name, at, frames) {
  return `<!doctype html><meta charset="utf-8"><style>
  body { margin: 0; padding: 16px; width: max-content; background: #ececef; color: #18181b; font: 13px/1.3 ui-monospace, Menlo, Consolas, monospace; }
  h1 { font: inherit; margin: 0 0 10px; color: #55555c; }
  .grid { display: grid; grid-template-columns: repeat(${ACROSS}, auto); gap: 12px; }
  figure { margin: 0; }
  figcaption { margin: 0 0 6px; }
  img { display: block; outline: 1px solid #c9c9ce; }
</style><h1>hairline-${esc(name)} · the answer while it plays, the pointer to at=${esc(at)} after the first picture</h1>
<div class="grid">${frames.map((f) => `<figure><figcaption>${esc(f.label)}</figcaption><img src="data:image/png;base64,${f.png}"></figure>`).join("")}</div>`;
}

/** Whether a box leaves the 400 × 320 viewBox. */
const outside = (b) => b.x < 0 || b.y < 0 || b.x + b.w > 400 || b.y + b.h > 320;
const n0 = (v) => Math.round(v);

/** The look of one figure (a .js, built here, or a page build.mjs made). Prints as it goes and returns the exit code. */
export async function look(src, given0 = {}, cwd = process.cwd()) {
  let { answer = null, edge = [] } = given0;
  const { zoom = null, source = null } = given0;
  if (zoom && !SHOTS.some(([s]) => s === zoom)) { console.error(`look: no shot "${zoom}". The shots: ${SHOTS.map(([s]) => s).join(", ")}.`); return 2; }
  /* the source is read before anything is built, so a wrong path costs nothing; read.mjs imports this file, so it is imported here, when needed */
  let sourceXml = null, sourceInfo = null;
  if (source) {
    try { sourceXml = readFileSync(source, "utf8"); } catch { console.error(`look: cannot read the source ${resolve(source)}`); return 2; }
    const { scan } = await import("./read.mjs");
    sourceInfo = scan(sourceXml, basename(source));
    if (sourceInfo.error) { console.error(`look: ${sourceInfo.error}`); return 2; }
  }

  // 1. the page, built and validated
  let file, page;
  try { page = readFileSync(src, "utf8"); } catch { console.error(`look: cannot read ${src}`); return 2; }
  if (src.endsWith(".html")) file = resolve(src);
  else {
    file = join(cwd, `hairline-${nameOf(page) ?? "figure"}.html`);
    page = assemble(page);
    writeFileSync(file, page);
  }
  const name = /^hairline-(.+)\.html$/.exec(basename(file))?.[1] ?? basename(file, ".html");
  const problems = validate(page);
  if (problems.length) {
    for (const p of problems) console.log(p);
    console.log(`${problems.length} to fix in ${file}. Fix the figure and run this again; no browser was opened.`);
    return 1;
  }
  console.log(`${src.endsWith(".html") ? "read" : "built"} ${file}, and the validator passes it`);

  // the browser, from the cache
  const dir = cacheDir();
  let pw;
  try { pw = playwright(dir); } catch (e) {
    console.error(`look: could not install playwright-core into ${dir}: ${e.message}`);
    console.error('Check the network and run this again, or look without a browser: look.md, "Without a browser".');
    return 2;
  }
  const browser = await launch(pw).catch(() => null);
  if (!browser) {
    console.error(`look: no Chrome, and no Chromium of Playwright's. Install one once:\n  node "${pw.cli}" install chromium`);
    console.error('Then run this again. Without a browser, look.md says what to do: "Without a browser".');
    return 2;
  }

  try {
    const url = pathToFileURL(file).href, address = (q) => (q ? `${url}?${q}` : url);

    // 2. the points, through the figure's own P, from the rest page
    const context = await window800(browser);
    const rest = await open(context, url, true);
    // the points the figure gives in its hairline({ … }) call, if any; a point on the command line wins over them
    const decl = (await rest.page.evaluate(() => window.declared ?? null)) ?? { answer: null, edge: null }, theirs = new Set();
    const isPoint = (p) => Array.isArray(p) && (p.length === 2 || p.length === 3) && p.every((v) => typeof v === "number" && Number.isFinite(v));
    if (!answer && decl.answer) {
      if (isPoint(decl.answer)) theirs.add((answer = decl.answer));
      else console.log(`the figure's hairline call gives answer ${[decl.answer].flat().join(",")}, which is not a point: two numbers for the viewBox, three for the world. Give --answer x,y,z instead.`);
    }
    if (!edge.length && decl.edge) {
      const list = Array.isArray(decl.edge[0]) ? decl.edge : [decl.edge];
      if (list.length <= 2 && list.every(isPoint)) for (const p of (edge = list)) theirs.add(p);
      else console.log(`the figure's hairline call gives edge ${JSON.stringify(decl.edge)}, which is not one point or two. Give --edge x,y,z instead.`);
    }
    const given = { answer, low: edge[0] ?? answer, high: edge[1] ?? edge[0] ?? answer }, at = {}, said = [];
    for (const [key, p] of Object.entries({ answer, edge0: edge[0], edge1: edge[1] })) {
      if (!p) continue;
      const v = p.length === 2 ? p : await rest.page.evaluate((q) => (window.P ? window.P(...q).map(Math.round) : null), p);
      if (!v) { said.push(`${p} -> no P: the figure stopped before it called HL.proj`); continue; }
      for (const use of Object.keys(given)) if (given[use] === p) at[use] = v.join(",");
      said.push(`${key === "answer" ? "answer" : "edge"} ${p}${theirs.has(p) ? " (from the figure's hairline call)" : ""} -> at=${v.join(",")}`);
    }
    if (said.length) console.log(said.join(" · "));
    if (!answer) console.log("no --answer: the answering shots are taken at rest. Give --answer x,y,z, a world point on the part that should answer.");
    else if (!edge.length) console.log(`no --edge: the slider's two ends are taken with the pointer at the ${theirs.has(answer) ? "answer" : "--answer"} point.`);

    // 3. the other seven, and the zoom, opened at once; each waits from its own load, so the waits overlap
    const queryOf = (q, use) => [q, use && at[use] && `at=${at[use]}`].filter(Boolean).join("&");
    const taking = SHOTS.map(async ([shot, q, use]) => {
      const query = queryOf(q, use);
      const s = { name: shot, query, answering: !!(use && at[use]), ...(shot === "rest" ? rest : await open(context, address(query))) };
      s.held = await settle(s);
      Object.assign(s, await s.page.evaluate(STATE));
      s.png = (await s.page.screenshot({ clip: s.clip })).toString("base64");
      return s;
    });
    const zooming = zoom && (async () => {
      const [, q, use] = SHOTS.find(([s]) => s === zoom), z = await open(await window800(browser, 3), address(queryOf(q, use)));
      await settle(z);
      const png = join(cwd, `hairline-${name}-${zoom}.png`);
      await z.page.screenshot({ path: png, clip: (await z.page.evaluate(STATE)).stage });
      return png;
    })();
    const shots = await Promise.all(taking), zoomOut = zoom ? await zooming : null;
    let sourceShot = null;
    if (sourceXml) {
      const { snapshot } = await import("./read.mjs");
      sourceShot = { file: basename(source), png: (await snapshot(browser, sourceXml, sourceInfo.viewBox)).png };
    }

    // 4. the sheet, composed in the browser
    for (const s of shots) s.label = `${s.name}  ${s.query ? "?" + s.query : "(plain)"}  read: ${s.read}${s.box && outside(s.box) ? "  OUT OF FRAME" : ""}`;
    const out = join(cwd, `hairline-${name}-look.png`);
    const board = await (await browser.newContext({ viewport: { width: 1400, height: 800 } })).newPage();
    await board.setContent(sheet(name, shots, sourceShot));
    await board.evaluate(() => Promise.all([...document.images].map((i) => i.decode())));
    await board.screenshot({ path: out, fullPage: true });

    // the blind pair: the two thumbnails' stages with the name and the read-out hidden, for a reader who was told nothing
    const unnamed = async (s) => {
      await s.page.addStyleTag({ content: "#name, #read { visibility: hidden }" });
      return (await s.page.screenshot({ clip: s.stage })).toString("base64");
    };
    const small = (n) => shots.find((s) => s.name === n);
    const blind = [await unnamed(small("small")), await unnamed(small("small-answer"))];
    const blindOut = join(cwd, `hairline-${name}-blind.png`);
    const pair = await (await browser.newContext({ viewport: { width: 600, height: 300 } })).newPage();
    await pair.setContent(`<!doctype html><meta charset="utf-8"><style>body { margin: 0; padding: 12px; display: flex; gap: 12px; align-items: flex-start; width: max-content; background: #ececef; } img { display: block; outline: 1px solid #c9c9ce; }</style>${blind.map((b) => `<img src="data:image/png;base64,${b}">`).join("")}`);
    await pair.evaluate(() => Promise.all([...document.images].map((i) => i.decode())));
    await pair.locator("body").screenshot({ path: blindOut });
    const share = moved(await pair.evaluate(INK, [blind[0], INKED]), await pair.evaluate(INK, [blind[1], INKED]));

    // the motion strip: the rest page, held still, given the pointer at the answer point as ?at= gives it, and taken while it plays
    const motion = [];
    let motionOut = null;
    if (at.answer) {
      const stage = shots[0], snap = async () => (await stage.page.screenshot({ clip: stage.stage })).toString("base64");
      motion.push({ label: "rest", png: await snap() });
      await stage.page.evaluate(POINT, at.answer);
      const t0 = Date.now();
      for (const t of beats().slice(1)) {
        await sleep(t0 + t - Date.now());
        const ms = Date.now() - t0;
        motion.push({ label: `${ms}ms`, png: await snap() });
      }
      motionOut = join(cwd, `hairline-${name}-motion.png`);
      const film = await (await browser.newContext({ viewport: { width: 1400, height: 800 } })).newPage();
      await film.setContent(strip(name, at.answer, motion));
      await film.evaluate(() => Promise.all([...document.images].map((i) => i.decode())));
      await film.screenshot({ path: motionOut, fullPage: true });
    }

    // 5. what can be measured
    let failed = false;
    const fail = (line) => { failed = true; console.log(line); };

    const away = shots.filter((s) => s.box && outside(s.box));
    const box = shots[0].box;
    const fills = box && `Rest fills ${n0(box.w)} × ${n0(box.h)}, ${n0((100 * box.w * box.h) / 128000)}% of it`;
    if (!box) fail("9 frame: fail. The rest shot's svg is empty: the figure drew nothing.");
    else if (away.length) {
      const x0 = Math.min(...away.map((s) => s.box.x)), x1 = Math.max(...away.map((s) => s.box.x + s.box.w));
      const y0 = Math.min(...away.map((s) => s.box.y)), y1 = Math.max(...away.map((s) => s.box.y + s.box.h));
      fail(`9 frame: fail. ${away.length === shots.length ? "Every shot" : away.map((s) => s.name).join(", ")} leaves the 400 × 320 viewBox: the drawing reaches x ${n0(x0)} to ${n0(x1)} and y ${n0(y0)} to ${n0(y1)}.`);
    } else {
      const small = (box.w * box.h) / 128000 < SMALL;
      console.log(`9 frame: ${small ? "warn" : "ok"}. Every shot stays inside the 400 × 320 viewBox. ${fills}${small ? `; the examples' cover 36%. Raise S, or say why the figure is small` : ""}.`);
    }

    const reads = shots.map((s) => `${s.name} "${s.read}"`).join(", ");
    const still = shots.filter((s) => s.answering && ["answer", "small-answer", "dark", "light"].includes(s.name) && s.read === "rest");
    if (shots[0].read !== "rest") fail(`8 read-out: fail. At rest it says "${shots[0].read}", not "rest". ${reads}.`);
    else console.log(`8 read-out: ${still.length ? `warn. ${still.map((s) => s.name).join(", ")} still say "rest": the --answer point is not on the part, or the hit test misses it` : "ok"}. ${reads}.`);

    // each complaint once, with the shots that made it
    const noise = new Map();
    for (const s of shots) for (const b of [...s.bad, ...(s.error ? [`error line under the stage: ${s.error}`] : [])]) noise.set(b, [...(noise.get(b) ?? []), s.name]);
    const heard = [...noise].map(([b, where]) => `${b} (${where.length === shots.length ? "every shot" : where.join(", ")})`);
    if (heard.length) fail(`12 console: fail. ${heard.slice(0, 4).join("; ")}${heard.length > 4 ? `; and ${heard.length - 4} more` : ""}.`);
    else console.log("12 console: ok. No console error or warning, no page error, no error line under the stage.");

    // a drawing that never held still: a flicker loop, an ambient figure, or a machine too busy to finish the motion in time
    const restless = shots.filter((s) => s.held === null), slowest = Math.max(...shots.map((s) => s.held ?? 0));
    console.log(`4 flicker: ${restless.length
      ? `moving. ${restless.length === shots.length ? "Every shot" : restless.map((s) => s.name).join(", ")} still moving ${CAP / 1000} seconds after loading${shots[0].held === null ? "" : ", while rest held still"}`
      : `still. Every shot held still within ${slowest.toFixed(1)} seconds of loading`}. Information, not a check: look.md, item 4.`);


    // how much of the thumbnail the answer moves: a warning, never a fail
    if (!answer) console.log("3 answer: not measured. No --answer.");
    else {
      const faint = share < FAINT;
      console.log(`3 answer: ${faint ? "warn" : "ok"}. At 240px the pointer moves ${n0(share * 100)}% of the ink, the pixels drawn in one small picture and not the other, over those drawn at rest${faint ? `; under ${n0(FAINT * 100)}% the answer is hard to see in a thumbnail. A change of colour moves no ink: make the answer move more, or say why a small one is right` : ""}.`);
    }

    if (sourceShot) console.log(`source ${resolve(source)} is on the sheet beside rest: look.md, item 14.`);
    console.log(`sheet ${out}`);
    console.log(`blind ${blindOut} holds the small and small-answer pictures with the name and the read-out hidden, as someone who has not seen the figure would meet it: for item 1, look at it that way, or show it to such a reader.`);
    if (motionOut) console.log(`motion ${motionOut} is the stage while the answer plays: ${motion.length} pictures, rest first, then each labelled with the ms since the pointer reached the answer point. The sheet shows only pictures that held still, so a part that folds, crosses another part, or jumps between two frames on the way is seen only here: look for one, and fix it in the figure.`);
    if (zoomOut) console.log(`zoom ${zoomOut}`);
    return failed ? 1 : 0;
  } finally {
    await browser.close();
  }
}

/** Whether two resolved paths are one file. Windows paths ignore case, and the drive letter's case can differ between the two. */
export const same = (a, b, platform = process.platform) => platform === "win32" ? a.toLowerCase() === b.toLowerCase() : a === b;

/* The skill is often installed as a symlink, so the path Node was given is resolved before it is compared. */
if (process.argv[1] && same(realpathSync(process.argv[1]), realpathSync(here("./look.mjs")))) {
  let args;
  try {
    args = parseArgs({ allowPositionals: true, options: { answer: { type: "string" }, edge: { type: "string", multiple: true }, zoom: { type: "string" }, source: { type: "string" } } });
  } catch (e) {
    console.error(`${e.message}\n${USAGE}`);
    process.exit(2);
  }
  const { positionals: [src], values } = args;
  const answer = values.answer === undefined ? null : point(values.answer);
  const edge = (values.edge ?? []).map(point);
  if (!src || (values.answer !== undefined && !answer) || edge.some((p) => !p) || edge.length > 2) {
    console.error(USAGE);
    process.exit(2);
  }
  process.exit(await look(src, { answer, edge, zoom: values.zoom ?? null, source: values.source ?? null }));
}

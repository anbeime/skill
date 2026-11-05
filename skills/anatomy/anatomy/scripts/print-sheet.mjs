export const PAPER = {
  a4: { name: "A4", w: 210, h: 297, px: [794, 1123] },
  letter: { name: "Letter", w: 215.9, h: 279.4, px: [816, 1056] },
};

export const FORMATS = ["poster", "drawing", "detailed"];

export const DIM = { hi: "#cdcdd1", mid: "#dddde0", lo: "#e9e9eb", dot: "#d2d2d6" };
export const ON = { hi: "#000000", mid: "#2a2a2e", lo: "#707076", dot: "#000000" };
export const TONES = ["hi", "mid", "lo", "dot"];

const MM = 96 / 25.4;
const MARGIN = 16;
const PIN_GAP = 4.4;

const esc = (text) => String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const round = (value) => Math.round(value * 10) / 10;
const two = (n) => String(n).padStart(2, "0");
const LETTERS = "ABCDEFGH";

export function fitAspect([x, y, w, h], aspect) {
  if (w / h < aspect) {
    const grow = h * aspect - w;
    return [x - grow / 2, y, w + grow, h].map(round);
  }
  const grow = w / aspect - h;
  return [x, y - grow / 2, w, h + grow].map(round);
}

export function pad([x, y, w, h], share) {
  const p = Math.max(w, h) * share;
  return [x - p, y - p, w + 2 * p, h + 2 * p].map(round);
}

export function boxOf(view, ids, padBy = 0) {
  const boxes = ids.map((id) => view.boxes?.[id]).filter(Boolean);
  if (!boxes.length) throw new Error(`no boxes for ${ids.join(", ")}`);
  const x0 = Math.min(...boxes.map((b) => b[0])) - padBy;
  const y0 = Math.min(...boxes.map((b) => b[1])) - padBy;
  const x1 = Math.max(...boxes.map((b) => b[2])) + padBy;
  const y1 = Math.max(...boxes.map((b) => b[3])) + padBy;
  return [x0, y0, x1 - x0, y1 - y0].map(round);
}

export function frameOf(view) {
  return view.raster ? view.raster.region : view.content ? pad(view.content, 0.02) : view.vb;
}

export function focusCrop(view, ids, aspect, frame, least = 0.42) {
  const box = pad(boxOf(view, ids), 0.18);
  const minW = frame[2] * least;
  const grown = box[2] < minW ? [box[0] - (minW - box[2]) / 2, box[1], minW, box[3]] : box;
  const [x, y, w, h] = fitAspect(grown, aspect);
  const cx = Math.max(frame[0], Math.min(frame[0] + frame[2] - w, x));
  const cy = Math.max(frame[1], Math.min(frame[1] + frame[3] - h, y));
  return [w > frame[2] ? x : cx, h > frame[3] ? y : cy, w, h].map(round);
}

export function relax(pins, minGap, rounds = 80) {
  const out = pins.map((pin) => ({ ...pin, pos: [...pin.at] }));
  for (let round = 0; round < rounds; round++) {
    let moved = false;
    for (let i = 0; i < out.length; i++) {
      for (let j = i + 1; j < out.length; j++) {
        const a = out[i].pos;
        const b = out[j].pos;
        let dx = b[0] - a[0];
        let dy = b[1] - a[1];
        let d = Math.hypot(dx, dy);
        if (d >= minGap) continue;
        if (d < 1e-6) {
          dx = Math.cos(i + j);
          dy = Math.sin(i + j);
          d = 1;
        }
        const push = (minGap - d) / 2 + 1e-3;
        a[0] -= (dx / d) * push;
        a[1] -= (dy / d) * push;
        b[0] += (dx / d) * push;
        b[1] += (dy / d) * push;
        moved = true;
      }
    }
    if (!moved) break;
  }
  return out;
}

export function layerTable(views) {
  const ids = new Map();
  const defs = [];
  const refs = {};
  for (const [name, view] of Object.entries(views)) {
    refs[name] = (view.layers ?? []).map((html) => {
      if (!ids.has(html)) {
        const id = `pl${ids.size}`;
        ids.set(html, id);
        defs.push(`<g id="${id}">${html}</g>`);
      }
      return ids.get(html);
    });
  }
  return { defs: defs.join(""), refs };
}

function useStyle({ focus, hide }) {
  let style = "";
  if (focus?.length) {
    style += TONES.map((tone) => `--anatomy-${tone}:${DIM[tone]};--part-${tone}:${DIM[tone]}`).join(";") + ";";
    style += focus.map((id) => TONES.map((tone) => `--on-${id}-${tone}:${ON[tone]}`).join(";")).join(";") + ";";
  }
  if (hide?.length) style += hide.map((id) => `--show-${id}:none`).join(";") + ";";
  return style;
}

export function figure(ctx, use, { crop, widthMm, pins = [], marks = [], weight }) {
  const view = ctx.views[use.view];
  if (!view) throw new Error(`no captured view "${use.view}"`);
  const [x, y, w, h] = crop ?? frameOf(view);
  const perMm = w / widthMm;
  const lineWeight = weight ?? Math.max(0.32, Math.min(0.6, ((widthMm * MM) / w) * 0.9));
  let art;
  if (view.raster) {
    const [rx, ry, rw, rh] = view.raster.region;
    art = `<image href="${view.raster.href}" x="${rx}" y="${ry}" width="${rw}" height="${rh}" preserveAspectRatio="none"/>`;
  } else {
    const layers = use.layers ?? ctx.refs[use.view].map((_, index) => index);
    const style = useStyle(use);
    art = layers.map((index) => `<use href="#${ctx.refs[use.view][index]}"${style ? ` style="${style}"` : ""}/>`).join("");
  }
  const placed = relax(pins, PIN_GAP * perMm);
  const leaders = placed
    .filter((pin) => Math.hypot(pin.pos[0] - pin.at[0], pin.pos[1] - pin.at[1]) > 1.6 * perMm)
    .map((pin) => `<line x1="${round(pin.at[0])}" y1="${round(pin.at[1])}" x2="${round(pin.pos[0])}" y2="${round(pin.pos[1])}"/><circle cx="${round(pin.at[0])}" cy="${round(pin.at[1])}" r="${round(0.55 * perMm)}"/>`)
    .join("");
  const markSvg = marks
    .map((mark) => `<circle class="ps-mark" cx="${round(mark.c[0])}" cy="${round(mark.c[1])}" r="${round(mark.r)}"/>`)
    .join("");
  const overlay = leaders || markSvg ? `<svg class="ps-over" viewBox="${x} ${y} ${w} ${h}" preserveAspectRatio="xMidYMid meet">${markSvg}${leaders}</svg>` : "";
  const pct = (px, py) => `left:${round(((px - x) / w) * 100)}%;top:${round(((py - y) / h) * 100)}%`;
  const pinHtml = placed.map((pin) => `<span class="ps-pin" style="${pct(...pin.pos)}">${pin.n}</span>`).join("");
  const markHtml = marks.map((mark) => `<span class="ps-pin ps-letter" style="${pct(mark.c[0] + mark.r * 0.71, mark.c[1] - mark.r * 0.71)}">${mark.label}</span>`).join("");
  return `<div class="ps-fig" style="aspect-ratio:${w}/${h};--anatomy-weight:${lineWeight.toFixed(2)}"><svg class="iso-svg" viewBox="${x} ${y} ${w} ${h}" preserveAspectRatio="xMidYMid meet">${art}</svg>${overlay}${pinHtml}${markHtml}</div>`;
}

function mainOf(ctx) {
  const main = ctx.spec.main;
  const view = ctx.views[main.view];
  if (!view) throw new Error(`no captured view "${main.view}"`);
  return { main, view, crop: main.crop ?? frameOf(view) };
}

function pinsOf(ctx, view) {
  return ctx.parts.map((part, index) => ({ n: index + 1, at: part.at ?? view.anchors?.[part.id] })).filter((pin) => pin.at);
}

function detailsOf(ctx) {
  return (ctx.spec.details ?? []).map((detail, index) => {
    const view = ctx.views[detail.view ?? ctx.spec.main.view];
    const crop = detail.crop ?? fitAspect(pad(boxOf(view, detail.around), 0.14), 1);
    return { ...detail, view: detail.view ?? ctx.spec.main.view, crop, label: LETTERS[index] };
  });
}

function numbersHtml(spec, cls = "ps-num") {
  return (spec.numbers ?? []).map(([n, unit, label]) => `<div class="${cls}"><b>${esc(n)}<small>${esc(unit)}</small></b><span>${esc(label)}</span></div>`).join("");
}

function legendHtml(ctx) {
  return ctx.parts.map((part, index) => `<li><span>${two(index + 1)}</span><div><b>${esc(part.name)}</b>${part.say ? `<i>${esc(part.say)}</i>` : ""}</div></li>`).join("");
}

const BASE_CSS = (paper) => `
@page{size:${paper.w}mm ${paper.h}mm;margin:0}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#e9e9e6}
body{-webkit-print-color-adjust:exact;print-color-adjust:exact}
.iso[data-theme="light"]{--anatomy-paper:#ffffff;--anatomy-card:#ffffff;--anatomy-face:#ffffff}
.ps{width:${paper.w}mm;height:${paper.h}mm;margin:0 auto;background:#fff;overflow:hidden;color:#151517;padding:${MARGIN}mm ${MARGIN}mm 12mm;font-family:"Helvetica Neue",Helvetica,Arial,sans-serif;break-after:page;position:relative}
.ps:last-of-type{break-after:auto}
@media screen{html:not(.ps-bare) .ps{margin:10mm auto;box-shadow:0 1px 2px #0002,0 8px 30px #0001}html.ps-bare,html.ps-bare body{background:#fff}}
@media print{html,body{background:#fff}.ps{margin:0;box-shadow:none}}
.ps-fig{position:relative;width:100%}
.ps-fig>svg{position:absolute;inset:0;width:100%;height:100%;overflow:hidden;display:block}
.ps-fig>svg.ps-over{overflow:visible;pointer-events:none}
.ps-over line{stroke:#151517;stroke-width:.5px;vector-effect:non-scaling-stroke}
.ps-over circle{fill:#151517}
.ps-over .ps-mark{fill:none;stroke:#151517;stroke-width:.6px;stroke-dasharray:2 2;vector-effect:non-scaling-stroke}
.ps-pin{position:absolute;transform:translate(-50%,-50%);width:3.6mm;height:3.6mm;border-radius:50%;background:#151517;color:#fff;display:grid;place-items:center;font:500 6pt/1 "Helvetica Neue",Helvetica,Arial,sans-serif;font-variant-numeric:tabular-nums;box-shadow:0 0 0 .4mm #fff}
.ps-letter{background:#fff;color:#151517;box-shadow:0 0 0 .2mm #151517}
.ps-mono{font:400 6pt/1.5 Menlo,ui-monospace,monospace;letter-spacing:.1em;text-transform:uppercase;color:#8a8a8f}
.ps-fit{min-height:0;container-type:size}
.ps-fit>.ps-fig{width:min(100cqw,calc(100cqh * var(--ps-aspect)))}
.ps-ft{display:flex;justify-content:space-between;gap:6mm}
`;

function posterPage(ctx, paper) {
  const { spec } = ctx;
  const { main, view, crop } = mainOf(ctx);
  const figW = 112;
  const css = `
.pp{display:grid;grid-template-columns:54mm 1fr;grid-template-rows:auto minmax(0,1fr) auto auto;column-gap:8mm}
.pp-mast{grid-column:1/-1;display:flex;align-items:flex-end;justify-content:space-between;gap:6mm}
.pp-mast h1{margin:0;font-size:52pt;line-height:.86;font-weight:500;letter-spacing:-.045em}
.pp-mast .ps-mono{text-align:right}
.pp-side{padding-top:10mm;display:flex;flex-direction:column}
.pp-q{font-size:12pt;line-height:1.15;font-weight:500;letter-spacing:-.01em;margin:0 0 3mm}
.pp-lead{font-size:7.8pt;line-height:1.5;margin:0 0 9mm;color:#55555b}
.ps-num{padding:2.6mm 0;border-top:.15mm solid #d4d4d6}
.ps-num:last-child{border-bottom:.15mm solid #d4d4d6}
.ps-num b{display:block;font-size:17pt;line-height:1;letter-spacing:-.03em;font-weight:500}
.ps-num small{font-size:7.5pt;font-weight:400;margin-left:.8mm;letter-spacing:0;color:#55555b}
.ps-num span{display:block;margin-top:1mm;font:400 5.8pt/1.3 Menlo,ui-monospace,monospace;letter-spacing:.08em;text-transform:uppercase;color:#8a8a8f}
.pp-art{padding-top:6mm;display:flex;justify-content:center;align-items:flex-start}
.pp-art>div{width:100%;height:100%}
.pp-legend{grid-column:1/-1;margin:4mm 0 0;padding:5mm 0 0;border-top:.15mm solid #151517;list-style:none;columns:3;column-gap:6mm}
.pp-legend li{break-inside:avoid;display:grid;grid-template-columns:6mm 1fr;margin-bottom:2.4mm}
.pp-legend li>span{font:400 6.2pt/1.5 Menlo,ui-monospace,monospace;color:#8a8a8f}
.pp-legend b{display:block;font-size:7.2pt;font-weight:500;line-height:1.3}
.pp-legend i{display:block;font-style:normal;font-size:6.6pt;line-height:1.35;color:#77777d}
.pp .ps-ft{grid-column:1/-1;margin-top:3mm}
.pp-wide{grid-template-columns:1fr 1fr;grid-template-rows:auto auto minmax(0,1fr) auto auto}
.pp-wide .pp-art{grid-column:1/-1;grid-row:2;padding-top:8mm;height:auto}
.pp-wide .pp-art>div{height:auto;container-type:normal}.pp-wide .pp-art .ps-fig{width:100%}
.pp-wide .pp-side{grid-column:1/-1;grid-row:3;padding-top:6mm;display:grid;grid-template-columns:1fr 1fr;column-gap:10mm;align-content:start}
.pp-wide .pp-side>div{display:grid;grid-template-columns:1fr 1fr;column-gap:6mm;align-content:start}
`;
  const tags = [spec.number, "How it works", spec.tagline].filter(Boolean).map(esc).join("<br>");
  const wide = crop[2] / crop[3] > 1.15;
  const html = `<main class="ps pp${wide ? " pp-wide" : ""}">
<header class="pp-mast"><h1>${esc(spec.name)}</h1><div class="ps-mono">${tags}</div></header>
<aside class="pp-side">${spec.question ? `<p class="pp-q">${esc(spec.question)}</p>` : ""}${spec.lead ? `<p class="pp-lead">${esc(spec.lead)}</p>` : ""}<div>${numbersHtml(spec)}</div></aside>
<div class="pp-art"><div class="ps-fit" style="--ps-aspect:${round((crop[2] / crop[3]) * 1000) / 1000}">${figure(ctx, main, { crop, widthMm: Math.min(figW, 190 * (crop[2] / crop[3])), pins: pinsOf(ctx, view) })}</div></div>
<ol class="pp-legend">${legendHtml(ctx)}</ol>
<footer class="ps-ft ps-mono"><span>Anatomy</span><span>${esc(spec.quote ?? "")}</span><span>${paper.name}</span></footer>
</main>`;
  return { css, html };
}

function drawingPage(ctx, paper) {
  const { spec } = ctx;
  const { main, view, crop } = mainOf(ctx);
  const inner = paper.w - MARGIN * 2;
  const mainW = 106;
  const gap = 8;
  const sideW = inner - mainW - gap;
  const seqH = 34;
  const steps = spec.steps ?? [];
  const frameW = (inner - 5 * (steps.length - 1)) / Math.max(1, steps.length);
  const aspect = frameW / seqH;
  const list = ctx.parts.map((part, index) => `<li><span>${two(index + 1)}</span>${esc(part.name)}</li>`).join("");
  const rows = (spec.spec ?? []).map(([key, value]) => `<div><dt>${esc(key)}</dt><dd>${esc(value)}</dd></div>`).join("");
  let inset = "";
  if (spec.inset) {
    const insetView = ctx.views[spec.inset.view];
    const insetCrop = spec.inset.crop ?? frameOf(insetView);
    const width = Math.min(sideW, 52 * (insetCrop[2] / insetCrop[3]));
    inset = `<section class="pd-inset"><div class="ps-mono">${esc(spec.inset.label)}</div><div style="width:${round(width)}mm">${figure(ctx, spec.inset, { crop: insetCrop, widthMm: width })}</div></section>`;
  }
  const seq = steps
    .map((step, index) => {
      const stepView = ctx.views[step.view];
      const frame = step.frame ?? (stepView.raster ? stepView.raster.region : main.view === step.view ? crop : frameOf(stepView));
      const stepCrop = step.crop ?? (step.focus?.length && !stepView.raster ? focusCrop(stepView, step.focus, aspect, frame) : fitAspect(frame, aspect));
      return `<div class="pd-step"><div class="pd-frame"><div style="width:${round(frameW)}mm">${figure(ctx, step, { crop: stepCrop, widthMm: frameW, weight: 0.42 })}</div></div><p><span>${two(index + 1)}</span>${esc(step.title)}</p></div>`;
    })
    .join("");
  const css = `
.pd{display:grid;grid-template-columns:${mainW}mm ${sideW}mm;grid-template-rows:auto minmax(0,1fr) auto auto;column-gap:${gap}mm}
.pd-hd{grid-column:1/-1;display:flex;justify-content:space-between;align-items:flex-end;gap:6mm;padding-bottom:5mm;border-bottom:.15mm solid #151517}
.pd-hd h1{margin:1.6mm 0 0;font-size:17pt;font-weight:500;letter-spacing:-.015em;line-height:1.1}
.pd-no{text-align:right;white-space:nowrap}
.pd-no b{display:block;font:500 17pt/1.1 "Helvetica Neue",Helvetica,Arial,sans-serif;letter-spacing:-.01em;color:#151517;text-transform:none;margin-top:1.6mm}
.pd-main{padding-top:7mm}
.pd-main>.ps-fit{width:100%;height:100%}
.pd-side{padding-top:7mm;display:flex;flex-direction:column;gap:7mm;min-height:0}
.pd-side ol{list-style:none;margin:2.4mm 0 0;padding:0}
.pd-side li{display:grid;grid-template-columns:6mm 1fr;font-size:7.2pt;line-height:1.25;padding:.9mm 0}
.pd-side li span{font:400 6.4pt/1.4 Menlo,ui-monospace,monospace;color:#8a8a8f}
.pd-side dl{margin:2.4mm 0 0}
.pd-side dl div{display:grid;grid-template-columns:18mm 1fr;font-size:7.2pt;padding:.9mm 0}
.pd-side dt{color:#8a8a8f}.pd-side dd{margin:0}
.pd-inset{margin-top:auto}
.pd-inset .ps-fig{margin-top:2mm}
.pd-seq{grid-column:1/-1;padding-top:5mm;border-top:.15mm solid #151517;display:grid;grid-template-columns:repeat(${Math.max(1, steps.length)},1fr);column-gap:5mm}
.pd-frame{height:${seqH}mm;display:grid;place-items:center;overflow:hidden}
.pd-step p{margin:1.8mm 0 0;font-size:7pt;line-height:1.3}
.pd-step p span{display:block;font:400 6pt/1.4 Menlo,ui-monospace,monospace;color:#8a8a8f;margin-bottom:.4mm}
.pd .ps-ft{grid-column:1/-1;margin-top:6mm}
`;
  const html = `<main class="ps pd">
<div class="pd-hd"><div><div class="ps-mono">${esc(spec.kicker ?? "Explained drawing")}</div><h1>${esc(spec.title ?? spec.name)}</h1></div>${spec.number ? `<div class="pd-no ps-mono">Drawing<b>${esc(spec.number)}</b></div>` : ""}</div>
<div class="pd-main"><div class="ps-fit" style="--ps-aspect:${round((crop[2] / crop[3]) * 1000) / 1000}">${figure(ctx, main, { crop, widthMm: Math.min(mainW, 170 * (crop[2] / crop[3])), pins: pinsOf(ctx, view) })}</div></div>
<div class="pd-side">${list ? `<section><div class="ps-mono">Parts</div><ol>${list}</ol></section>` : ""}${rows ? `<section><div class="ps-mono">Specification</div><dl>${rows}</dl></section>` : ""}${inset}</div>
${steps.length ? `<div class="pd-seq">${seq}</div>` : ""}
<div class="ps-ft ps-mono"><span>Anatomy</span><span>Not to scale</span><span>${paper.name} · 1 / 1</span></div>
</main>`;
  return { css, html };
}

function detailedPages(ctx, paper) {
  const { spec } = ctx;
  const { main, view, crop } = mainOf(ctx);
  const details = detailsOf(ctx);
  const marks = details
    .filter((detail) => detail.view === main.view && detail.around)
    .map((detail) => {
      const [bx, by, bw, bh] = boxOf(view, detail.around);
      const only = detail.around.length === 1 ? ctx.parts.find((part) => part.id === detail.around[0]) : null;
      const c = detail.mark ?? only?.at ?? (only && view.anchors?.[only.id]) ?? [bx + bw / 2, by + bh / 2];
      return { c, r: Math.min(Math.hypot(bw, bh) / 2 + 4, crop[2] * 0.13), label: detail.label };
    });
  const steps = spec.steps ?? [];
  const thumb = 54;
  const wideMain = crop[2] / crop[3] > 1.15;
  const stepsHtml = steps
    .map((step, index) => {
      const stepView = ctx.views[step.view];
      const frame = step.frame ?? (stepView.raster ? stepView.raster.region : main.view === step.view ? crop : frameOf(stepView));
      const stepCrop = step.crop ?? (step.focus?.length && !stepView.raster ? focusCrop(stepView, step.focus, 1, frame, 0.36) : fitAspect(frame, 1));
      return `<div class="pe-step"><div class="pe-thumb">${figure(ctx, step, { crop: stepCrop, widthMm: thumb, weight: 0.45 })}</div><div><span class="pe-n">${two(index + 1)}</span><h3>${esc(step.title)}</h3>${step.text ? `<p>${esc(step.text)}</p>` : ""}</div></div>`;
    });
  const detailHtml = details
    .map((detail) => `<figure class="pe-detail"><div class="pe-ring">${figure(ctx, detail, { crop: detail.crop, widthMm: 30, weight: 0.55 })}</div><figcaption><span class="ps-pin ps-letter pe-tag">${detail.label}</span><b>${esc(detail.title)}</b>${detail.text ? `<i>${esc(detail.text)}</i>` : ""}</figcaption></figure>`)
    .join("");
  const rows = (spec.spec ?? []).map(([key, value]) => `<div><dt>${esc(key)}</dt><dd>${esc(value)}</dd></div>`).join("");
  const tags = [spec.number, spec.tagline].filter(Boolean).map(esc).join("<br>");
  const css = `
.pe1{display:grid;grid-template-columns:1fr 62mm;grid-template-rows:auto minmax(0,1fr) auto;column-gap:8mm}
.pe-left{display:flex;flex-direction:column;min-height:0}
${wideMain ? ".pe-left>.pe-art{flex:0 0 auto}.pe-left>.pe-art>.ps-fit{height:auto;container-type:normal}.pe-left .ps-fig{width:100%}.pe-left .pe-sub{margin-top:8mm}" : ""}
.pe-left>.pe-art{flex:1;min-height:0}
.pe-mast{grid-column:1/-1;display:flex;align-items:flex-end;justify-content:space-between;gap:6mm;padding-bottom:5mm;border-bottom:.15mm solid #151517}
.pe-mast h1{margin:0;font-size:40pt;line-height:.9;font-weight:500;letter-spacing:-.04em}
.pe-mast .ps-mono{text-align:right}
.pe-art{padding-top:7mm}
.pe-art>.ps-fit{width:100%;height:100%}
.pe-side{padding-top:7mm;display:flex;flex-direction:column;min-height:0}
.pe-q{font-size:11pt;line-height:1.18;font-weight:500;letter-spacing:-.01em;margin:0 0 2.4mm}
.pe-lead{font-size:7.5pt;line-height:1.5;margin:0 0 5mm;color:#55555b}
.pe-nums{display:grid;grid-template-columns:1fr 1fr;column-gap:4mm;margin-bottom:6mm}
.pe-num{padding:2mm 0;border-top:.15mm solid #d4d4d6}
.pe-num b{display:block;font-size:13pt;line-height:1;letter-spacing:-.025em;font-weight:500}
.pe-num small{font-size:6.6pt;font-weight:400;margin-left:.6mm;color:#55555b;letter-spacing:0}
.pe-num span{display:block;margin-top:.8mm;font:400 5.4pt/1.3 Menlo,ui-monospace,monospace;letter-spacing:.07em;text-transform:uppercase;color:#8a8a8f}
.pe-legend{list-style:none;margin:2mm 0 0;padding:0}
.pe-legend li{display:grid;grid-template-columns:6mm 1fr;padding:1.1mm 0;border-top:.15mm solid #ececee}
.pe-legend li>span{font:400 6pt/1.5 Menlo,ui-monospace,monospace;color:#8a8a8f}
.pe-legend b{display:block;font-size:7pt;font-weight:500;line-height:1.3}
.pe-legend i{display:block;font-style:normal;font-size:6.4pt;line-height:1.35;color:#77777d}
.pe1 .ps-ft,.pe2 .ps-ft{grid-column:1/-1;margin-top:5mm}
.pe2{display:flex;flex-direction:column}
.pe-top{display:flex;justify-content:space-between;align-items:flex-end;padding-bottom:4mm;border-bottom:.15mm solid #151517}
.pe-top h2{margin:0;font-size:17pt;font-weight:500;letter-spacing:-.015em}
.pe-steps{display:grid;grid-template-columns:1fr 1fr;column-gap:8mm;row-gap:7mm;padding-top:7mm}
.pe-step{display:grid;grid-template-columns:${thumb}mm 1fr;column-gap:4mm;align-items:start}
.pe-thumb{width:${thumb}mm;height:${thumb}mm;display:grid;place-items:center;overflow:hidden;background:#f7f7f6;border-radius:1.4mm}
.pe-thumb .ps-fig{width:${thumb}mm}
.pe-n{font:400 6pt/1.4 Menlo,ui-monospace,monospace;color:#8a8a8f}
.pe-step h3{margin:.6mm 0 1.4mm;font-size:10pt;font-weight:500;letter-spacing:-.01em;line-height:1.2}
.pe-step p{margin:0;font-size:7.8pt;line-height:1.5;color:#3a3a40}
.pe-sub{margin-top:5mm;padding-top:3.4mm;border-top:.15mm solid #151517}
.pe-details{display:grid;grid-template-columns:repeat(${Math.max(1, details.length)},1fr);column-gap:5mm;margin-top:3mm}
.pe-detail{margin:0}
.pe-ring{width:30mm;height:30mm;border-radius:50%;overflow:hidden;box-shadow:0 0 0 .2mm #151517;display:grid;place-items:center;background:#fff}
.pe-ring .ps-fig{width:30mm}
.pe-detail figcaption{margin-top:2.4mm;position:relative;padding-left:5.6mm}
.pe-tag{position:absolute;left:1.8mm;top:2mm}
.pe-detail b{display:block;font-size:7.6pt;font-weight:500;line-height:1.3}
.pe-detail i{display:block;font-style:normal;font-size:6.8pt;line-height:1.4;color:#55555b;margin-top:.6mm}
.pe-end{margin-top:auto;display:grid;grid-template-columns:40mm 1fr;column-gap:8mm;padding-top:4mm;border-top:.15mm solid #151517}
.pe-why{align-self:center;padding:5mm;border-left:.15mm solid #151517}
.pe-why h4{margin:0 0 2mm}
.pe-why p{margin:0;font-size:8.4pt;line-height:1.5;color:#151517}
.pe-end dl{margin:0;columns:2;column-gap:8mm}
.pe-end dl div{display:grid;grid-template-columns:18mm 1fr;font-size:6.9pt;padding:.6mm 0;break-inside:avoid}
.pe-end dt{color:#8a8a8f}.pe-end dd{margin:0}
`;
  const page1 = `<main class="ps pe1">
<header class="pe-mast"><h1>${esc(spec.name)}</h1><div class="ps-mono">${tags}<br>How it works · 1 / 2</div></header>
<div class="pe-left"><div class="pe-art"><div class="ps-fit" style="--ps-aspect:${round((crop[2] / crop[3]) * 1000) / 1000}">${figure(ctx, main, { crop, widthMm: Math.min(108, 165 * (crop[2] / crop[3])), pins: pinsOf(ctx, view), marks })}</div></div>${details.length ? `<section class="pe-sub"><div class="ps-mono">Close-ups</div><div class="pe-details">${detailHtml}</div></section>` : ""}</div>
<aside class="pe-side">${spec.question ? `<p class="pe-q">${esc(spec.question)}</p>` : ""}${spec.lead ? `<p class="pe-lead">${esc(spec.lead)}</p>` : ""}<div class="pe-nums">${numbersHtml(spec, "pe-num")}</div><div class="ps-mono">Parts</div><ol class="pe-legend">${legendHtml(ctx)}</ol></aside>
<footer class="ps-ft ps-mono"><span>Anatomy</span><span>${esc(spec.quote ?? "")}</span><span>${paper.name} · 1 / 2</span></footer>
</main>`;
  const plan = detailedPlan(spec);
  const total = plan.total;
  const why = spec.why ? `<div class="pe-why"><h4 class="ps-mono">${esc(spec.why.title)}</h4><p>${esc(spec.why.text)}</p></div>` : "";
  const stepHtml = stepsHtml;
  const pages = [page1];
  let at = 0;
  for (let n = 0; n < plan.stepPages; n++) {
    const pageNo = pages.length + 1;
    const take = stepHtml.slice(at, at + STEPS_PER_PAGE);
    at += take.length;
    const last = n === plan.stepPages - 1;
    pages.push(`<main class="ps pe2">
<div class="pe-top"><h2>How it works${plan.stepPages > 1 ? ` <span class="pe-cont">${n + 1} / ${plan.stepPages}</span>` : ""}</h2><div class="ps-mono">${esc(spec.name)} · ${paper.name} · ${pageNo} / ${total}</div></div>
<div class="pe-steps">${take.join("")}${last ? why : ""}</div>
${last && rows && !plan.assemblyPages ? `<section class="pe-end"><div class="ps-mono">Specification</div><dl>${rows}</dl></section>` : ""}
<footer class="ps-ft ps-mono"><span>Anatomy</span><span>Not to scale</span><span>${paper.name} · ${pageNo} / ${total}</span></footer>
</main>`);
  }
  const assemblies = (spec.assemblies ?? []).slice(0, plan.assemblyPages * ASSEMBLIES_PER_PAGE);
  for (let n = 0; n < plan.assemblyPages; n++) {
    const pageNo = pages.length + 1;
    const group = assemblies.slice(n * ASSEMBLIES_PER_PAGE, (n + 1) * ASSEMBLIES_PER_PAGE);
    const cards = group
      .map((a) => {
        const v = ctx.views[a.view ?? main.view];
        const frame = v.raster ? v.raster.region : (a.view ?? main.view) === main.view ? crop : frameOf(v);
        const c = a.crop ?? focusCrop(v, a.parts, 1, frame, 0.3);
        const nums = a.parts.map((id) => ctx.parts.findIndex((part) => part.id === id) + 1).filter((x) => x > 0).sort((x, y) => x - y);
        const pins = pinsOf(ctx, v).filter((pin) => nums.includes(pin.n));
        return `<article class="pe-asm"><div class="pe-asm-art">${figure(ctx, { view: a.view ?? main.view, layers: a.layers ?? main.layers, hide: a.hide ?? main.hide, focus: a.parts }, { crop: c, widthMm: ASM_W, pins, weight: 0.5 })}</div><h3>${esc(a.title)}</h3>${a.text ? `<p>${esc(a.text)}</p>` : ""}${nums.length ? `<div class="ps-mono pe-asm-parts">Parts ${nums.map(two).join(" · ")}</div>` : ""}</article>`;
      })
      .join("");
    const last = n === plan.assemblyPages - 1;
    pages.push(`<main class="ps pe2">
<div class="pe-top"><h2>Assemblies</h2><div class="ps-mono">${esc(spec.name)} · ${paper.name} · ${pageNo} / ${total}</div></div>
<div class="pe-asms">${cards}</div>
${last && rows ? `<section class="pe-end"><div class="ps-mono">Specification</div><dl>${rows}</dl></section>` : ""}
<footer class="ps-ft ps-mono"><span>Anatomy</span><span>Not to scale</span><span>${paper.name} · ${pageNo} / ${total}</span></footer>
</main>`);
  }
  const extra = `
.pe-cont{font:400 7pt/1 Menlo,ui-monospace,monospace;color:#8a8a8f;letter-spacing:.08em;margin-left:2mm;vertical-align:middle}
.pe-asms{display:grid;grid-template-columns:1fr 1fr;column-gap:8mm;row-gap:7mm;padding-top:7mm}
.pe-asm-art{width:${ASM_W}mm;height:${ASM_W}mm;display:grid;place-items:center;overflow:hidden;background:#f7f7f6;border-radius:1.4mm}
.pe-asm-art .ps-fig{width:${ASM_W}mm}
.pe-asm h3{margin:3mm 0 1.2mm;font-size:10pt;font-weight:500;letter-spacing:-.01em}
.pe-asm p{margin:0;font-size:7.6pt;line-height:1.5;color:#3a3a40}
.pe-asm-parts{margin-top:1.6mm}
.pe-asms+.pe-end{margin-top:6mm}
`;
  return { css: css + extra, html: pages.join("").replace(/How it works · 1 \/ 2/, `How it works · 1 / ${total}`).replace(/(<span>)A4 · 1 \/ 2(<\/span>)/, `$1${paper.name} · 1 / ${total}$2`).replace(new RegExp(`${paper.name} · 1 / 2`, "g"), `${paper.name} · 1 / ${total}`) };
}

const STEPS_PER_PAGE = 6;
const ASSEMBLIES_PER_PAGE = 4;
const ASM_W = 80;

export function detailedPlan(spec) {
  const steps = (spec.steps ?? []).length;
  const slots = steps + (spec.why ? 1 : 0);
  const stepPages = Math.max(1, Math.ceil(slots / STEPS_PER_PAGE));
  let assemblyPages = Math.ceil((spec.assemblies ?? []).length / ASSEMBLIES_PER_PAGE);
  const cap = Math.max(2, Math.min(4, spec.maxPages ?? 4));
  if (1 + stepPages > cap) throw new Error(`${steps} steps need ${1 + stepPages} pages, over maxPages ${cap}; cut steps`);
  assemblyPages = Math.min(assemblyPages, cap - 1 - stepPages);
  return { stepPages, assemblyPages, total: 1 + stepPages + assemblyPages };
}

const LAYOUTS = { poster: posterPage, drawing: drawingPage, detailed: detailedPages };

export function sheetHtml(capture, spec, paper = PAPER.a4, format = spec.format ?? "poster") {
  const layout = LAYOUTS[format];
  if (!layout) throw new Error(`unknown format "${format}"; use one of ${FORMATS.join(", ")}`);
  const { defs, refs } = layerTable(capture.views);
  const ctx = { views: capture.views, refs, spec, parts: (spec.parts ?? []).filter((part) => part.name) };
  const { css, html } = layout(ctx, paper);
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(spec.title ?? spec.name)}</title><script>if(location.search.includes("print"))document.documentElement.classList.add("ps-bare")</script><style>${capture.css ?? ""}</style><style>${BASE_CSS(paper)}${css}</style></head><body class="iso" data-theme="light"><svg width="0" height="0" aria-hidden="true" style="position:absolute"><defs>${defs}</defs></svg>${html}</body></html>`;
}

export function pagesOf(format, spec = {}) {
  return format === "detailed" ? detailedPlan(spec).total : 1;
}

"use client";

import { useEffect, useRef } from "react";

type Pt = [number, number];

/** The floor's isometric projection, at 30px a unit. Every point is projected here, so each stroke is one screen pixel whatever its direction. */
const C = Math.cos(Math.PI / 6), S = 0.5, K = 30;
const P = (x: number, y: number, z = 0): Pt => [K * C * (x - y), K * S * (x + y) - z];

const NS = "http://www.w3.org/2000/svg";
const mk = (tag: string, at: Record<string, string | number>, parent: Element) => {
  const el = document.createElementNS(NS, tag) as SVGElement;
  for (const k in at) el.setAttribute(k, String(at[k]));
  parent.appendChild(el);
  return el;
};
const f = (n: number) => n.toFixed(2);
const line = (pts: Pt[]) => "M" + pts.map((p) => f(p[0]) + "," + f(p[1])).join("L");
const clamp = (v: number) => Math.max(0, Math.min(1, v));
/** A critically damped spring from 0 to 1: it leaves rest with no jolt and settles on a long, soft tail. */
const spring = (t: number, w: number) => (t <= 0 ? 0 : 1 - (1 + w * t) * Math.exp(-w * t));
const inout = (t: number) => ((t = clamp(t)) < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const out = (t: number) => 1 - Math.pow(1 - clamp(t), 3);

/** A rounded rectangle on the floor, as points: four quarter arcs, n steps each. */
function ring(x0: number, y0: number, x1: number, y1: number, r: number, n = 8): Pt[] {
  const pts: Pt[] = [];
  for (const [cx, cy, a0] of [[x1 - r, y0 + r, -90], [x1 - r, y1 - r, 0], [x0 + r, y1 - r, 90], [x0 + r, y0 + r, 180]]) {
    for (let i = 0; i <= n; i++) {
      const a = ((a0 + (90 * i) / n) * Math.PI) / 180;
      pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]);
    }
  }
  return pts;
}

/** The rim's points split at its left and right extremes on screen: the half nearer the viewer is the side you see. */
function frontHalf(pts: Pt[]) {
  let l = 0, r = 0;
  pts.forEach((p, i) => {
    if (p[0] < pts[l][0]) l = i;
    if (p[0] > pts[r][0]) r = i;
  });
  const walk = (a: number, b: number) => {
    const o: Pt[] = [];
    for (let i = a; ; i = (i + 1) % pts.length) {
      o.push(pts[i]);
      if (i === b) break;
    }
    return o;
  };
  const h1 = walk(l, r), h2 = walk(r, l), avg = (h: Pt[]) => h.reduce((s, p) => s + p[1], 0) / h.length;
  return avg(h1) > avg(h2) ? h1 : h2.reverse();
}

/** The window, half-widths A × B with corners of R; each plate T thick, its underside at rest at Z. N is the floor's reach. */
const A = 3.4, B = 2.4, R = 0.6, T = 6, Z = [22, 64, 106], N = 7;
const RIM = ring(-A, -B, A, B, R, 10);

/**
 * The window's parts, by stage: 0 the frame, 1 the blocks, 2 the details. The frame's lines run exactly to the rim and
 * sit under its stroke, so each meets the edge without a gap or a tip; the lit line is drawn over the grey row it marks.
 */
type Part = { stage: number; pts: Pt[]; cls: string; closed: boolean };
const TB = -B + 0.78, SB = -A + 1.45;
const PARTS: Part[] = [];
const add = (stage: number, pts: Pt[], cls = "part", closed = false) => PARTS.push({ stage, pts, cls, closed });
add(0, [[-A, TB], [A, TB]]);
add(0, [[SB, TB], [SB, B]]);
[0.72, 0.5, 0.62, 0.42].forEach((w, k) => add(1, [[-A + 0.4, TB + 0.55 + k * 0.42], [-A + 0.4 + w, TB + 0.55 + k * 0.42]]));
add(1, ring(SB + 0.4, TB + 0.42, A - 0.4, TB + 1.62, 0.16, 6), "part", true);
[3.3, 2.6, 3.0, 1.9].forEach((w, k) => add(1, [[SB + 0.4, TB + 2.12 + k * 0.42], [SB + 0.4 + w, TB + 2.12 + k * 0.42]]));
for (let k = 0; k < 3; k++) {
  const x = -A + 0.38 + k * 0.3, y = -B + 0.39, r = 0.085;
  add(2, ring(x - r, y - r, x + r, y + r, r, 6), "part pip", true);
}
add(2, [[SB + 0.75, TB + 0.82], [SB + 2.6, TB + 0.82]]);
add(2, ring(SB + 0.75, TB + 1.1, SB + 1.85, TB + 1.34, 0.12, 6), "part", true);
add(2, [[SB + 0.4, TB + 2.54], [SB + 3, TB + 2.54]], "lit");

/**
 * When things happen, in ms from mount. The floor starts at D, once the hero's own fade has shown the box; the first
 * plate at RISE, then one every STEP, each peeling off the top of the one below while that one is still settling.
 * At REST everything has arrived, and the stack starts to breathe.
 */
const D = 650, RISE = D + 900, STEP = 620, REST = RISE + 2 * STEP + 1100;

function build(host: HTMLElement) {
  const svg = mk("svg", { viewBox: "-380 -215 760 388", "aria-hidden": "true" }, host);
  const defs = mk("defs", {}, svg);
  const fade = mk("radialGradient", { id: "assembly-fade", cx: 0, cy: 0, r: 1, gradientUnits: "userSpaceOnUse" }, defs);
  mk("stop", { offset: 0.45, "stop-color": "#fff" }, fade);
  mk("stop", { offset: 1, "stop-color": "#fff", "stop-opacity": 0 }, fade);
  const mask = mk("mask", { id: "assembly-mask", maskUnits: "userSpaceOnUse", x: -400, y: -240, width: 800, height: 480 }, defs);
  mk("rect", { x: -400, y: -240, width: 800, height: 480, fill: "url(#assembly-fade)" }, mask);

  // the floor: a line every unit, each drawn as two halves running out from the point nearest the middle, and a dot
  // every quarter, seen through a soft disc that widens as they draw
  const floor = mk("g", { mask: "url(#assembly-mask)" }, svg);
  let d = "";
  for (let i = -N * 4; i <= N * 4; i++) {
    for (let j = -N * 4; j <= N * 4; j++) {
      if (i % 4 === 0 || j % 4 === 0) continue;
      const [x, y] = P(i / 4, j / 4);
      d += `M${f(x)},${f(y)}h.01`;
    }
  }
  const dots = mk("path", { d, class: "dots" }, floor);
  const rules: [SVGElement, number][] = [];
  for (let i = -N; i <= N; i++) {
    for (const e of [N, -N]) {
      rules.push([mk("path", { class: "rule", d: line([P(i, 0), P(i, e)]), pathLength: 1 }, floor), Math.abs(i)]);
      rules.push([mk("path", { class: "rule", d: line([P(0, i), P(e, i)]), pathLength: 1 }, floor), Math.abs(i)]);
    }
  }
  const foot = mk("path", { class: "foot", d: line(RIM.map((p) => P(p[0], p[1]))) + "Z" }, svg);
  const drop = mk("path", { class: "drop", d: line(ring(-A + 0.15, -B + 0.15, A - 0.15, B - 0.15, R).map((p) => P(p[0], p[1]))) + "Z" }, svg);

  // each plate carries every part up to its own stage; `k` counts the ones its own stage adds, -1 for those it inherits
  const plates = Z.map((_, i) => {
    const g = mk("g", {}, svg);
    const band = mk("path", { class: "band" }, g), side = mk("path", { class: "edge" }, g), face = mk("path", { class: "face" }, g);
    const pg = mk("g", {}, g);
    let n = 0;
    const parts = PARTS.filter((w) => w.stage <= i).map((w) => ({ ...w, k: w.stage === i ? n++ : -1, el: mk("path", { class: w.cls, pathLength: 1 }, pg) }));
    return { g, band, side, face, parts, top: mk("path", { class: "edge" }, g) };
  });
  return { fade, rules, dots, foot, drop, plates };
}

type Scene = ReturnType<typeof build>;

/** The floor's entrance: the disc widens while the lines run out to meet its edge, the nearer ones first. */
function drawFloor(s: Scene, t: number) {
  const k = N * (0.1 + 0.9 * out((t - D) / 1500));
  s.fade.setAttribute("gradientTransform", `matrix(${f(K * C * k)} ${f(K * S * k)} ${f(-K * C * k)} ${f(K * S * k)} 0 0)`);
  for (const [el, d] of s.rules) {
    const p = out((t - D - d * 55) / 1000);
    el.style.strokeDashoffset = String(1 - p);
    el.style.opacity = p ? "1" : "0";
  }
  s.dots.style.opacity = String(out((t - D - 200) / 1200));
}

/** At rest the stack breathes as one body: the gaps open and close together, slowly, rising from nothing. */
const breath = (t: number) => Math.sin(((t - REST) / 1000) * 1.05) * inout((t - REST) / 2400);

/** One frame at `t`: where each plate's underside is, how thick it is, and how much of what it adds is drawn yet. */
function draw(s: Scene, t: number, still: boolean) {
  const b = still ? 0 : breath(t);
  let below = 0, lift = 0;
  s.plates.forEach((pl, i) => {
    const u = (t - RISE - i * STEP) / 1000;
    const z = below + (Z[i] - below) * spring(u, 5.2) + b * (1.4 + 1.6 * i), th = T * out(u / 0.6);
    if (!i) lift = z;
    below = z + th;
    pl.g.style.opacity = String(i ? (u >= 0 ? 1 : 0) : clamp(u / 0.25));
    const top = RIM.map((p) => P(p[0], p[1], z + th)), bot = RIM.map((p) => P(p[0], p[1], z));
    const fb = frontHalf(bot), ft = frontHalf(top), rim = line(top) + "Z";
    pl.band.setAttribute("d", line([...ft, ...fb.slice().reverse()]) + "Z");
    pl.side.setAttribute("d", line(fb) + line([ft[0], fb[0]]) + line([ft[ft.length - 1], fb[fb.length - 1]]));
    pl.side.style.opacity = th > 0.2 ? "1" : "0";
    pl.face.setAttribute("d", rim);
    pl.top.setAttribute("d", rim);
    for (const w of pl.parts) {
      const p = w.k < 0 ? 1 : out((t - RISE - i * STEP - 260 - w.k * 55) / 520);
      w.el.setAttribute("d", line(w.pts.map((q) => P(q[0], q[1], z + th))) + (w.closed ? "Z" : ""));
      w.el.style.strokeDashoffset = String(1 - p);
      w.el.style.opacity = p ? "1" : "0";
    }
  });
  s.foot.style.opacity = String(inout((t - D - 450) / 700));
  // the shadow on the floor darkens as the bottom plate lifts off it
  s.drop.style.opacity = String(0.55 * clamp(lift / Z[0]));
}

/**
 * The hero's drawing: a floor that draws itself out from the middle, then a window built as three plates that peel
 * off one another, the frame, then the blocks, then the details, each adding its stage as it rises. Once built, the
 * stack breathes. One clock drives it all; it only counts the time the drawing is on screen, so a hidden tab or a
 * scroll away picks up where it left off. Under reduced motion it is drawn at rest, at once.
 */
export function Assembly() {
  const host = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = host.current!;
    const scene = build(el);
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
      drawFloor(scene, REST);
      draw(scene, REST, true);
      return () => el.replaceChildren();
    }
    let t = 0, prev = 0, raf = 0;
    const tick = (now: number) => {
      // a long gap (a slow frame, a tab coming back) counts as one ordinary frame
      t += prev ? Math.min(now - prev, 50) : 0;
      prev = now;
      if (t < REST) drawFloor(scene, t);
      draw(scene, t, false);
      raf = requestAnimationFrame(tick);
    };
    drawFloor(scene, 0);
    draw(scene, 0, false);
    const io = new IntersectionObserver(([e]) => {
      cancelAnimationFrame(raf);
      prev = 0;
      if (e.isIntersecting) raf = requestAnimationFrame(tick);
    });
    io.observe(el);
    return () => {
      io.disconnect();
      cancelAnimationFrame(raf);
      el.replaceChildren();
    };
  }, []);

  return <div ref={host} className="assembly" data-assembly />;
}

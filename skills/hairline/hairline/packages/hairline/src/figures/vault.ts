import { Cam, circ, clamp, fit, hull, lerp, open, poly, proj, rrect, run, seg, type Projector, type Ring, type Sample, type Vec2, type Vec3 } from "../core/iso";
import { reducedMotion, tdone, tset, tval, tween, type Tween } from "../core/motion";
import { disposer, mk, place, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";

/**
 * Vault: a round vault door standing proud of a wall block, a combination dial
 * at its centre and three bolts on its lock side, each thrown across a gap into
 * a keeper bolted to the wall. Circling the pointer round the dial pushes it;
 * it coasts, friction bleeds the spin, and a detent every ten catches it. When
 * it lands on forty the bolts draw back into the door, staggered out from the
 * one nearest the pointer, and they are thrown again once the dial leaves.
 * At rest the dial sits on thirty, the combination's long tick bright just
 * past the index. The slider is the coast: friction's time constant, in ms.
 *
 * The pattern: push the camera, as Turntable's: friction, then a spring into
 * the detent; tweens for the bolts' choice; a hit test on the door's own plane.
 */

const R = 40, DP = 14, ZC = 64, RD = 17, DT = 4, KN = 6, KH = 6, GAP = 10, KL = 11, KW = 12, KD = 10, BR = 3.6;
const HX = -R - 8, HR = 4.6, WX0 = -70, WX1 = 70, WZ1 = 130, WT = 14, COMBO = 40, REST = 30, STEP = 50, WMAX = 150;
const THETA = [72, 26, -20];
/** Toward the viewer, for Cam(45, 0.5): a face whose normal has a positive dot with it is seen. */
const V: Vec3 = [Math.SQRT1_2 * Math.sqrt(0.75), Math.SQRT1_2 * Math.sqrt(0.75), 0.5];
const dir = (deg: number): Vec3 => [Math.cos((deg * Math.PI) / 180), 0, Math.sin((deg * Math.PI) / 180)];
const wrap = (d: number) => ((((d + 50) % 100) + 100) % 100) - 50;

/**
 * A rounded solid along axis e from s0 to s1, its cross-section `ring` lying in
 * the (a, b) plane round o: the hull of its two ends, and one crease on the end
 * at s1 where it meets the side the viewer sees.
 */
function bar(P: Projector, o: Vec3, e: Vec3, a: Vec3, b: Vec3, ring: Ring, inner: Ring, s0: number, s1: number) {
  const at = (q: Sample, s: number) => P(
    o[0] + e[0] * s + a[0] * q.u + b[0] * q.v,
    o[1] + e[1] * s + a[1] * q.u + b[1] * q.v,
    o[2] + e[2] * s + a[2] * q.u + b[2] * q.v,
  );
  const seen = (q: Sample) => [0, 1, 2].reduce((t, i) => t + (a[i] * q.nu + b[i] * q.nv) * V[i], 0) > 0;
  return {
    sil: poly(hull(ring.map((q) => at(q, s0)).concat(ring.map((q) => at(q, s1))))),
    crease: open(run(inner, seen).map((q) => at(q, s1))),
  };
}

type Bolt = { th: number; e: Vec3; t: Vec3; el: Solid; tw: Tween; drawn: number };

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  let coast = value;
  const Y: Vec3 = [0, 1, 0], X: Vec3 = [1, 0, 0], Z: Vec3 = [0, 0, 1], O: Vec3 = [0, 0, ZC];

  const C = Cam(45, 0.5, 1.5);
  fit(C, [[WX0, -WT, 0], [WX1, -WT, 0], [WX0, -WT, WZ1], [WX1, -WT, WZ1], [WX0, KD, 0], [WX1, 0, 0], [WX0, 0, WZ1], [WX1, 0, WZ1]], 200, 166);
  const P = proj(C);

  const g = mk("g", {}, svg);
  // the wall block, then the door standing proud of it, painted back to front
  put(solid(g), bar(P, [0, 0, 0], Y, X, Z, rrect(WX0, 0, WX1, WZ1, 9, 6), rrect(WX0 + 2, 2, WX1 - 2, WZ1 - 2, 7, 6), -WT, 0));
  // the hinge, a barrel on the left with two arms into the door
  put(solid(g), bar(P, [HX, DP * 0.55, 0], Z, X, Y, circ(HR, 28), circ(HR - 1, 28), ZC - 26, ZC + 26));
  for (const dz of [-15, 15]) put(solid(g), bar(P, [0, 0, ZC + dz], Y, X, Z, rrect(HX, -4, -R + 6, 4, 3, 4), rrect(HX + 1, -3, -R + 5, 3, 2, 4), 1, DP * 0.8));
  put(solid(g), bar(P, O, Y, X, Z, circ(R, 72), circ(R - 2.4, 72), 0, DP));
  // the door's stepped face, and the index, a short stroke above the dial
  mk("path", { class: "nf lo", d: poly(circ(R - 8, 64).map((q) => P(q.u, DP, ZC + q.v))) }, g);
  mk("path", { class: "nf", d: seg(P(0, DP, ZC + RD + 1.8), P(0, DP, ZC + RD + 6.5)) }, g);
  const dial = solid(g);
  put(dial, bar(P, O, Y, X, Z, circ(RD, 56), circ(RD - 1.4, 56), DP, DP + DT));
  const ticks = mk("path", { class: "nf lo" }, g), longs = mk("path", { class: "nf" }, g), combo = mk("path", { class: "nf" }, g);
  put(solid(g), bar(P, O, Y, X, Z, circ(KN, 32), circ(KN - 1, 32), DP + DT, DP + DT + KH));

  // three bolts, each with the keeper it is thrown into; the keeper is painted after its bolt and covers its end
  const bolts: Bolt[] = THETA.map((th) => {
    const e = dir(th), t = dir(th + 90);
    const el = solid(g), keep = solid(g);
    put(keep, bar(P, O, Y, e, t, rrect(R + GAP, -KW / 2, R + GAP + KL, KW / 2, 3, 4), rrect(R + GAP + 1.4, -KW / 2 + 1.4, R + GAP + KL - 1.4, KW / 2 - 1.4, 1.8, 4), 0, KD));
    for (const s of [-3.4, 3.4]) {
      const c = R + GAP + KL / 2 + s;
      place(mk("circle", { r: 0.9, class: "dot off" }, keep.g), P(e[0] * c, KD, ZC + e[2] * c));
    }
    return { th, e, t, el, tw: tween(0), drawn: NaN };
  });
  const drawBolt = (b: Bolt, k: number) => {
    const s1 = lerp(R + GAP + 4.5, R + 1.2, k);
    if (s1 === b.drawn) return;
    b.drawn = s1;
    put(b.el, bar(P, [0, DP / 2, ZC], b.e, b.t, Y, circ(BR, 24), circ(BR - 0.9, 24), R - 0.2, s1));
  };

  // the dial: a is the number under the index, w its speed in numbers a second
  const spin = { a: REST, w: 0, mode: "rest" as "rest" | "coast" | "settle", tgt: REST };
  let raw = REST, said = "", last: number | null = null, lastT = 0, lastMove = -1e9, over = false, opened = false, from = 1, lit: string | null = null, drawnA = NaN;

  function drawDial() {
    if (spin.a === drawnA) return;
    drawnA = spin.a;
    const tk: string[] = [], lg: string[] = [], z = DP + DT;
    for (let m = 0; m < 100; m += 5) {
      const th = 90 + (m - spin.a) * 3.6, e = dir(th), r0 = m % 10 ? RD - 4 : RD - 6.5, r1 = RD - 1.8;
      const d = seg(P(e[0] * r0, z, ZC + e[2] * r0), P(e[0] * r1, z, ZC + e[2] * r1));
      if (m === COMBO) combo.setAttribute("d", d);
      else (m % 10 ? tk : lg).push(d);
    }
    ticks.setAttribute("d", tk.join(""));
    longs.setAttribute("d", lg.join(""));
  }

  /** One bright place: the bolts when open, the dial while handled, the combination's tick at rest. */
  function light() {
    const want = opened ? "bolts" : over ? "dial" : "combo";
    if (want === lit) return;
    lit = want;
    bolts.forEach((b) => b.el.sil.classList.toggle("hi", want === "bolts"));
    dial.sil.classList.toggle("hi", want === "dial");
    combo.classList.toggle("hi", want === "combo");
  }

  function setOpen(on: boolean, now: number) {
    opened = on;
    bolts.forEach((b, i) => tset(b.tw, on ? 1 : 0, now, Math.abs(i - from) * STEP));
    light();
  }

  /** Coast under friction, a detent's pull every ten; once slow, a spring into the nearest. 240Hz substeps. */
  function stepSpin(dt: number, now: number) {
    if (spin.mode === "rest") return false;
    const n = Math.max(1, Math.ceil(dt * 240)), h = dt / n;
    for (let i = 0; i < n; i++) {
      if (spin.mode === "coast") {
        spin.w = spin.w * Math.exp((-h * 1000) / coast) - 40 * Math.sin((spin.a / 10) * 2 * Math.PI) * h;
        spin.a += spin.w * h;
        if (Math.abs(spin.w) < 12 && now - lastMove > 90) { spin.mode = "settle"; spin.tgt = Math.round((spin.a + spin.w * 0.15) / 10) * 10; }
      } else { spin.w += (-90 * (spin.a - spin.tgt) - 16 * spin.w) * h; spin.a += spin.w * h; }
    }
    if (spin.mode === "settle" && Math.abs(spin.a - spin.tgt) < 0.01 && Math.abs(spin.w) < 0.2) {
      spin.a = spin.tgt = ((spin.tgt % 100) + 100) % 100; spin.w = 0; spin.mode = "rest";
    }
    return spin.mode !== "rest";
  }

  const B = register(stage, (dt, now) => {
    let m = stepSpin(dt, now);
    const near = Math.abs(wrap(spin.a - COMBO));
    if (!opened && near < 0.8 && Math.abs(spin.w) < 6) setOpen(true, now);
    else if (opened && near > 2.5) setOpen(false, now);
    drawDial();
    bolts.forEach((b) => { drawBolt(b, tval(b.tw, now)); if (!tdone(b.tw, now)) m = true; });
    const n = String(((Math.round(spin.a) % 100) + 100) % 100).padStart(2, "0");
    const say = over || spin.mode !== "rest" ? `dial ${n}` + (opened ? " · open" : "") : "rest";
    if (say !== said) read.textContent = said = say;
    return m;
  });
  bag.add(B.unregister);

  // the pointer on the door's face plane, which never moves
  const p0 = P(0, DP, 0), px = P(1, DP, 0), pz = P(0, DP, 1);
  const ax = [px[0] - p0[0], px[1] - p0[1]], az = [pz[0] - p0[0], pz[1] - p0[1]], det = ax[0] * az[1] - ax[1] * az[0];
  function onFace([sx, sy]: Vec2): Vec2 {
    const qx = sx - p0[0], qy = sy - p0[1];
    return [(qx * az[1] - qy * az[0]) / det, (ax[0] * qy - ax[1] * qx) / det - ZC];
  }

  function leave() {
    over = false; last = null;
    if (reducedMotion()) { raw = spin.a = ((Math.round(spin.a / 10) * 10) % 100 + 100) % 100; spin.w = 0; spin.mode = "rest"; }
    light(); B.wake();
  }

  bag.add(pointer(stage, {
    move: (p) => {
      const [u, v] = onFace(p), r = Math.hypot(u, v);
      if (r > R + GAP + KL + 10) return leave();
      const now = performance.now(), ang = (Math.atan2(v, u) * 180) / Math.PI;
      over = true;
      from = THETA.reduce((bi, th, i) => (Math.abs(wrap((ang - th) / 3.6)) < Math.abs(wrap((ang - THETA[bi]) / 3.6)) ? i : bi), 0);
      if (last !== null) {
        // circling the dial turns it with the pointer; near its centre the push fades
        const da = (-(((ang - last + 540) % 360) - 180) / 3.6) * clamp(r / 22, 0, 1);
        if (reducedMotion()) { raw += da; spin.a = Math.round(raw / 10) * 10; spin.mode = "rest"; }
        else {
          spin.w = clamp(lerp(spin.w, da / Math.max(0.008, (now - lastT) / 1000), 0.35), -WMAX, WMAX);
          spin.mode = "coast"; raw = spin.a;
        }
        if (Math.abs(da) > 0.05) lastMove = now;
      }
      last = ang; lastT = now;
      light(); B.wake();
    },
    leave,
  }));
  light();
  bag.add(() => svg.replaceChildren());

  return { set: (v) => { coast = v; B.wake(); }, destroy: bag.dispose };
};

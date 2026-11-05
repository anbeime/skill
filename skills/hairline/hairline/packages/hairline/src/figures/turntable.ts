import { Cam, circ, clamp, facing, lerp, prism, proj, r2, rad, rings, seg, type Ring } from "../core/iso";
import { reducedMotion, spring, stepS } from "../core/motion";
import { BLK, HOME, detent, order, type Blk } from "./turntable-geometry";
import { disposer, flatDot, mk, place, pointer, put, register, solid, type FigureMount, type Solid } from "../core/stage";

/**
 * Turntable — flick it round. The camera is the variable: moving across the
 * platter pushes its near edge, friction bleeds the spin off, and once it is
 * slow a spring pulls it into the nearest quarter-turn detent, so every stop
 * is 2:1 again. Pointer y springs the elevation. The blocks are re-ordered
 * every frame (lib/hairline/turntable-geometry.ts). From the study's sixth
 * figure (design/lab-hairline/cartilha-v2.html).
 *
 * The slider is `coast`: the friction's time constant, in ms.
 */

const RING = 70, PT = 4, WMAX = 540, ON_INDEX = 14;

type Block = { b: Blk; ring: Ring; inner: Ring };

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  let coast = value;

  // The platter's angle in degrees, its angular velocity, and whether it is coasting, settling or at rest.
  const spin = { a: HOME, w: 0, mode: "rest" as "rest" | "coast" | "settle", tgt: HOME };
  const kk = spring(0.5, { eps: 0.0005 });
  let lastX: number | null = null, lastT = 0, lastMove = -1e9;

  /** Coast under friction, then spring into the detent; 240Hz substeps so a long frame can't overshoot. */
  function stepSpin(dt: number, now: number) {
    if (spin.mode === "rest") return false;
    const n = Math.max(1, Math.ceil(dt * 240)), h = dt / n;
    for (let i = 0; i < n; i++) {
      if (spin.mode === "coast") {
        spin.w *= Math.exp((-h * 1000) / coast); spin.a += spin.w * h;
        if (Math.abs(spin.w) < 45 && now - lastMove > 90) { spin.mode = "settle"; spin.tgt = detent(spin.a + spin.w * 0.2); }
      } else { spin.w += (-90 * (spin.a - spin.tgt) - 16 * spin.w) * h; spin.a += spin.w * h; }
    }
    if (spin.mode === "settle" && Math.abs(spin.a - spin.tgt) < 0.02 && Math.abs(spin.w) < 0.3) { spin.a = spin.tgt; spin.w = 0; spin.mode = "rest"; }
    return spin.mode !== "rest";
  }

  const C = Cam(HOME, 0.5, 1.85); C.ox = 200; C.oy = 184;
  const plat = circ(RING), platIn = circ(RING - 1.5);
  const blocks: Block[] = BLK.map((b) => { const [ring, inner] = rings(b[0], b[1], b[3], b[4], 3, 1.1); return { b, ring, inner }; });
  const TALL = blocks.find((k) => k.b[5] >= 40)!;
  // each column lights by its top block only
  const tops: Record<number, Block> = {};
  blocks.forEach((k) => { if (!tops[k.b[6]] || k.b[5] > tops[k.b[6]].b[5]) tops[k.b[6]] = k; });
  const base: Record<number, [number, number]> = {};
  blocks.forEach((k) => { if (k.b[2] === 0) base[k.b[6]] = [(k.b[0] + k.b[3]) / 2, (k.b[1] + k.b[4]) / 2]; });

  const g = mk("g", {}, svg);
  const platter = solid(g), ticks = mk("path", { class: "nf lo" }, g), major = mk("path", { class: "nf" }, g);
  const north = flatDot(g, C, 1.7, "dot m");
  const index = mk("path", { class: "nf" }, g);
  const pool = BLK.map(() => solid(g));
  // The tall block's dot code: a 4 × 4 grid less its corners, the rim dots medium. It rides that block's lid,
  // so it is moved to just after whichever pool group the tall block is drawn in.
  const acc = mk("g", {}, g), accD: { r: number; q: number; el: SVGEllipseElement }[] = [];
  for (let k = 0; k < 16; k++) {
    const r = Math.floor(k / 4), q = k % 4, edge = r % 3 === 0, side = q % 3 === 0;
    if (edge && side) continue;
    accD.push({ r, q, el: flatDot(acc, C, 0.6, edge || side ? "dot m" : "dot") });
  }
  let accAt: Solid | null = null;

  const B = register(stage, (dt, now) => {
    let m = stepSpin(dt, now);
    if (stepS(kk, dt)) m = true;
    C.az = rad(spin.a); C.k = kk.x;
    const P = proj(C), front = facing(C), c = Math.cos(C.az), s = Math.sin(C.az);
    put(platter, prism(P, front, plat, platIn, -PT, 0));
    const tk: string[] = [], mj: string[] = [];
    for (let d = 0; d < 360; d += 15) {
      const a = rad(d), long = d % 90 === 0, r0 = long ? RING - 12 : RING - 8;
      (long ? mj : tk).push(seg(P(Math.cos(a) * r0, Math.sin(a) * r0, 0), P(Math.cos(a) * (RING - 4.5), Math.sin(a) * (RING - 4.5), 0)));
    }
    ticks.setAttribute("d", tk.join("")); major.setAttribute("d", mj.join(""));
    place(north, P(0, -(RING - 17), 0)); north.setAttribute("ry", String(r2(1.7 * C.S * C.k)));
    const bottom = C.oy + RING * C.S * C.k + PT * C.S * Math.sqrt(1 - C.k * C.k);
    index.setAttribute("d", `M${C.ox - 4} ${r2(bottom + 10)}L${C.ox} ${r2(bottom + 4)}L${C.ox + 4} ${r2(bottom + 10)}`);
    // while the platter is handled or turning, the column passing the index mark lights; at rest nothing does
    let lit = -1, best = ON_INDEX;
    if (lastX !== null || spin.mode !== "rest")
      for (const col in base) {
        const [x, y] = base[col], off = (Math.abs(Math.atan2(x * c - y * s, x * s + y * c)) * 180) / Math.PI;
        if (off < best) { best = off; lit = +col; }
      }
    order(BLK, s, c, C.k).forEach((j, i) => {
      const k = blocks[j];
      put(pool[i], prism(P, front, k.ring, k.inner, k.b[2], k.b[5]));
      pool[i].sil.classList.toggle("hi", k === tops[lit]);
      if (k === TALL && accAt !== pool[i]) { accAt = pool[i]; accAt.g.after(acc); }
    });
    const [x0, y0, , x1, y1, z1] = TALL.b, cx = (x0 + x1) / 2, cy = (y0 + y1) / 2;
    accD.forEach(({ r, q, el }) => {
      place(el, P(cx + (q - 1.5) * 2.6, cy + (r - 1.5) * 2.6, z1));
      el.setAttribute("ry", String(r2(0.6 * C.S * C.k)));
    });
    read.textContent = `az ${String(Math.round(((spin.a % 360) + 360) % 360)).padStart(3, "0")}° · el ${Math.round((Math.asin(kk.x) * 180) / Math.PI)}°`;
    return m;
  });
  bag.add(B.unregister);

  bag.add(pointer(stage, {
    move: (p) => {
      const now = performance.now();
      kk.t = lerp(Math.sin(rad(40)), Math.sin(rad(20)), clamp(p[1] / 320, 0, 1));
      if (lastX !== null) {
        const dx = p[0] - lastX;
        if (reducedMotion()) spin.a -= dx * 0.9;
        else {
          // pushing the near edge: the platter's front follows the pointer
          const vp = dx / Math.max(0.008, (now - lastT) / 1000);
          spin.w = clamp(lerp(spin.w, -vp * 0.9, 0.35), -WMAX, WMAX); spin.mode = "coast";
        }
        if (Math.abs(dx) > 0.5) lastMove = now;
      }
      lastX = p[0]; lastT = now; B.wake();
    },
    leave: () => { lastX = null; kk.t = 0.5; if (reducedMotion()) spin.a = detent(spin.a); B.wake(); },
  }));

  bag.add(() => svg.replaceChildren());
  return { set: (v) => { coast = v; B.wake(); }, destroy: bag.dispose };
};

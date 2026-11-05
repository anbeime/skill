import { Cam, clamp, fit, hull, open, poly, proj, rad, rrect, run, seg, unproj, type Ring, type Sample, type Vec2, type Vec3 } from "../core/iso";
import { spring, stepS } from "../core/motion";
import { disposer, mk, pointer, put, register, solid, type FigureMount } from "../core/stage";
import { TABLE } from "../intensity";

/**
 * Basket: a wire shopping basket. A rim and a floor, both solid, dim wires
 * standing between them, and a bail handle with a grip. The pointer tilts the
 * basket toward it on a spring, so the bare floor shows, and the handle
 * swings after it, late. At rest the basket stands level, the handle dropped
 * to one side, the rim bright; tilted, the bright goes to the floor. The
 * slider is the furthest tilt, in degrees.
 *
 * The pattern: a lean. Two springs hold the tilt as a vector on the ground,
 * set from the pointer on a fixed plane through the basket's middle, never
 * from the basket on screen. Everything turns about the floor's centre.
 * Tipped away from the camera it goes half as far, so the floor still shows.
 * The handle swings on a softer spring, as Rail's hangers, whose target is
 * read from the tilt as drawn: it comes late.
 */

const A = 40, B = 25, RR = 8, RT = 1.5, H = 30, F = 0.8;      // rim: half length, half width, corner radius, wire radius, height; the floor's size as a share of the rim's
const FT = 3, FB = 1.4, N = 44, BANDS = [0.45];               // floor: thickness, crease inset; wires round the wall; horizontal wires, as shares of the height
const HH = 30, HR = 8, HT = 1.3, GRIP = 9, GT = 2.6;          // handle: height over its pivots, corner radius, bar radius, grip half length, grip radius
const REST_H = -46, LIFT = 0.6, REACH = 70, S = 3;       // the handle's lean at rest, in degrees, and how far a degree of tilt lifts it; the pointer's distance for the full tilt; scale
type Rot = (x: number, y: number, z: number) => Vec3;

/** The tilt toward a ground direction by m degrees. Tipping away from the camera goes half as far, so the mouth stays open to it. */
function aim(dx: number, dy: number, m: number): Vec2 {
  const a = Math.min(0, (dx + dy) * Math.SQRT1_2) / 2;          // half the part of the direction that points away from the camera, which is at 45°
  return [m * (dx - a * Math.SQRT1_2), m * (dy - a * Math.SQRT1_2)];
}

/** The tilt as a rotation about the floor's centre: the mouth turns toward (tx, ty) by their length, in degrees. */
function tilter(tx: number, ty: number): Rot {
  const m = Math.hypot(tx, ty), kx = m ? -ty / m : 0, ky = m ? tx / m : 0, c = Math.cos(rad(m)), s = Math.sin(rad(m));
  return (x, y, z) => { const d = (kx * x + ky * y) * (1 - c); return [x * c + ky * z * s + kx * d, y * c - kx * z * s + ky * d, z * c + (kx * y - ky * x) * s]; };
}

/** n samples evenly spaced by length round a closed ring. */
function stations(ring: Ring, n: number): Ring {
  const L = [0];
  for (let i = 1; i <= ring.length; i++) { const p = ring[i - 1], q = ring[i % ring.length]; L.push(L[i - 1] + Math.hypot(q.u - p.u, q.v - p.v)); }
  return Array.from({ length: n }, (_, k) => {
    const s = (k / n) * L[ring.length];
    let i = 0;
    while (L[i + 1] < s) i++;
    const p = ring[i], q = ring[(i + 1) % ring.length], f = (s - L[i]) / (L[i + 1] - L[i] || 1);
    return { u: p.u + (q.u - p.u) * f, v: p.v + (q.v - p.v) * f, nu: p.nu, nv: p.nv };
  });
}

/** A round bar's outline on screen: its centre line offset by its radius. Closed, it is a ring with a hole; open, its ends are round. */
function tube(Q: readonly Vec2[], rho: number, closed = false): string {
  const n = Q.length, L: Vec2[] = [], R: Vec2[] = [], T: Vec2[] = [];
  for (let i = 0; i < n; i++) {
    const a = Q[closed ? (i + n - 1) % n : Math.max(i - 1, 0)], b = Q[closed ? (i + 1) % n : Math.min(i + 1, n - 1)];
    const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1, tx = (b[0] - a[0]) / l, ty = (b[1] - a[1]) / l;
    T.push([tx, ty]); L.push([Q[i][0] - ty * rho, Q[i][1] + tx * rho]); R.push([Q[i][0] + ty * rho, Q[i][1] - tx * rho]);
  }
  if (closed) return poly(L) + poly(R.reverse());
  /** Half a round about c, from the left side to the right, bulging along d. */
  const cap = (c: Vec2, t: Vec2, d: number) => Array.from({ length: 7 }, (_, k): Vec2 => {
    const th = (Math.PI * (k + 1)) / 8, co = Math.cos(th) * d, si = Math.sin(th) * d;
    return [c[0] + rho * (-t[1] * co + t[0] * si), c[1] + rho * (t[0] * co + t[1] * si)];
  });
  return poly([...L, ...cap(Q[n - 1], T[n - 1], 1), ...R.reverse(), ...cap(Q[0], T[0], -1)]);
}

/** The handle's centre line in its own plane: u across the basket, w up from the pivots. */
const ARM: Vec2[] = /* @__PURE__ */ (() => [[-B, 0], ...Array.from({ length: 9 }, (_, k): Vec2 => { const t = Math.PI - (Math.PI / 2) * (k / 8); return [-B + HR + HR * Math.cos(t), HH - HR + HR * Math.sin(t)]; }),
  ...Array.from({ length: 9 }, (_, k): Vec2 => { const t = (Math.PI / 2) * (1 - k / 8); return [B - HR + HR * Math.cos(t), HH - HR + HR * Math.sin(t)]; }), [B, 0]])();
const GRIPS: Vec2[] = [[-GRIP, HH], [GRIP, HH]];

/** A point of the handle's plane, swung phi degrees toward +x about the pivots, in the basket's own frame. */
const swing = (phi: number) => { const c = Math.cos(rad(phi)), s = Math.sin(rad(phi)); return (p: Vec2): Vec3 => [p[1] * s, p[0], H + p[1] * c]; };

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  const C = Cam(45, 0.5, S);
  const MAXT = TABLE.basket[2];          // the slider's far end: under the camera's 30°, so it still sees into the mouth
  const HMAX = REST_H + LIFT * MAXT;     // the handle's most upright: where the furthest tilt lifts it
  const rim = rrect(-A, -B, A, B, RR, 14), wires = stations(rim, N);
  const floor = rim.map((q): Sample => ({ ...q, u: q.u * F, v: q.v * F }));
  const lid = rrect(-A * F + FB, -B * F + FB, A * F - FB, B * F - FB, RR * F - FB, 14);

  // The frame holds every pose: the furthest tilt every way, with the handle at both ends of its swing.
  const ext: Vec3[] = [];
  for (let k = -1; k < 8; k++) {
    const R = tilter(...aim(Math.cos((k * Math.PI) / 4), Math.sin((k * Math.PI) / 4), k < 0 ? 0 : MAXT));
    for (const q of rim) ext.push(R(q.u, q.v, H + RT), R(q.u * F, q.v * F, 0));
    for (const phi of [REST_H, HMAX]) for (const p of ARM) ext.push(R(...swing(phi)(p)));
  }
  fit(C, ext, 200, 166);
  const P0 = proj(C), sw = Math.sqrt(1 - C.k * C.k), cam: Vec3 = [Math.sin(C.az) * sw, Math.cos(C.az) * sw, C.k];
  const g = mk("g", {}, svg);

  // Back to front: the far wall's wires, the floor, the near wall's wires, the rim, the handle and its grip.
  const far = mk("path", { class: "nf lo" }, g);
  const base = solid(g);
  const near = mk("path", { class: "nf lo" }, g);
  const ring = mk("path", { class: "sil" }, g);
  const bar = mk("path", { class: "sil" }, g);
  const grip = mk("path", { class: "sil" }, g);

  const tx = spring(0), ty = spring(0), hp = spring(REST_H, { k: 60, c: 6, eps: 0.02 });
  let dX = NaN, dY = NaN, dH = NaN, R = tilter(0, 0);
  const at = (p: Vec3) => P0(...R(...p));
  /** Whether a wall with this outward normal faces the camera, once tilted. */
  const facing = (q: Sample) => { const n = R(q.nu, q.nv, 0); return n[0] * cam[0] + n[1] * cam[1] + n[2] * cam[2] >= 0; };

  function draw() {
    const moved = tx.x !== dX || ty.x !== dY;
    if (moved) {
      dX = tx.x; dY = ty.x; R = tilter(dX, dY);
      put(base, {
        sil: poly(hull(floor.map((q) => at([q.u, q.v, 0])).concat(floor.map((q) => at([q.u, q.v, FT]))))),
        crease: open(run(lid, facing).map((q) => at([q.u, q.v, FT]))),
      });
      // the wires: up the wall from the floor's edge to the rim, and round it at each band's height
      const d = ["", ""];
      for (const q of wires) d[+facing(q)] += seg(at([q.u * F - q.nu, q.v * F - q.nv, FT]), at([q.u, q.v, H]));   // a foot just inside the floor's edge, off its outline
      for (const b of BANDS) {
        const z = FT + (H - FT) * b, k = F + (1 - F) * b;
        rim.forEach((q, i) => { const r = rim[(i + 1) % rim.length]; d[+facing(q)] += seg(at([q.u * k, q.v * k, z]), at([r.u * k, r.v * k, z])); });
      }
      far.setAttribute("d", d[0]); near.setAttribute("d", d[1]);
      ring.setAttribute("d", tube(rim.map((q) => at([q.u, q.v, H])), RT * S, true));
    }
    if (moved || hp.x !== dH) {
      dH = hp.x;
      const s = swing(dH);
      bar.setAttribute("d", tube(ARM.map((p) => at(s(p))), HT * S));
      grip.setAttribute("d", tube(GRIPS.map((p) => at(s(p))), GT * S));
    }
  }

  const loop = register(stage, (dt) => {
    const a = stepS(tx, dt), b = stepS(ty, dt);
    hp.t = Math.min(REST_H + LIFT * Math.hypot(tx.x, ty.x), HMAX);   // any tilt lifts it off the rim; it chases the tilt as drawn, so it comes late
    const c = stepS(hp, dt);
    draw();
    return a || b || c;
  });
  bag.add(loop.unregister);

  let tmax = value, over = false, gx = 0, gy = 0;
  function retarget() {
    const r = Math.hypot(gx, gy), m = over && r ? clamp(tmax, 0, MAXT) * clamp(r / REACH, 0, 1) : 0;
    [tx.t, ty.t] = m ? aim(gx / r, gy / r, m) : [0, 0];
    read.textContent = over ? `tilt ${Math.round(Math.hypot(tx.t, ty.t))}° · 0` : "rest";
    ring.classList.toggle("hi", !over);
    base.sil.classList.toggle("hi", over);
    loop.wake();
  }
  retarget();

  bag.add(pointer(stage, {
    // the pointer on a plane through the basket's middle, which never moves
    move: (p) => { over = true; [gx, gy] = unproj(C, p[0], p[1], H / 2); retarget(); },
    leave: () => { over = false; retarget(); },
  }));
  bag.add(() => svg.replaceChildren());

  return { set: (v) => { tmax = v; retarget(); }, destroy: bag.dispose };
};

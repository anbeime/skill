import {
  Cam, fit, proj, unproj, facing, rings, prism, rrect, ringAt, extremes, poly, seg, clamp, lerp,
  type Vec2,
} from "../core/iso";
import { reducedMotion } from "../core/motion";
import {
  mk, solid, put, flatDot, place, reflect, register, pointer, disposer,
  type FigureMount,
} from "../core/stage";

/**
 * Phosphor (Fig 9.4): a 7 × 7 dot matrix you can paint on. Each dot holds an
 * intensity that decays with persistence τ (the slider, in ms). At idle a
 * loop of frames, seven row bytes each, excites the dots; the pointer
 * excites them instead, and the loop fades back in 1.2s after it leaves.
 * Ambient: the tick always asks for another frame, so it runs whenever the
 * stage is on screen and the shared observer puts it to sleep when it isn't.
 * Ported from the study's `#phosphor` (design/lab-hairline/cartilha-v2.html).
 */

const N = 7, PITCH = 10, M = 8, EXT = M * 2 + PITCH * (N - 1), T = 5, R = 2.5, DROP = 15, BT = 4, BO = 7;
/** The loop, seven row bytes per frame (MSB = left column): a ripple out from the centre, a pause, a diagonal sweep, a pause. */
const LOOP = [
  [0, 0, 0, 8, 0, 0, 0], [0, 0, 8, 20, 8, 0, 0], [0, 28, 34, 34, 34, 28, 0], [28, 34, 65, 65, 65, 34, 28], [65, 0, 0, 0, 0, 0, 65],
  [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0],
  [64, 0, 0, 0, 0, 0, 0], [32, 64, 0, 0, 0, 0, 0], [16, 32, 64, 0, 0, 0, 0], [8, 16, 32, 64, 0, 0, 0], [4, 8, 16, 32, 64, 0, 0], [2, 4, 8, 16, 32, 64, 0], [1, 2, 4, 8, 16, 32, 64],
  [0, 1, 2, 4, 8, 16, 32], [0, 0, 1, 2, 4, 8, 16], [0, 0, 0, 1, 2, 4, 8], [0, 0, 0, 0, 1, 2, 4], [0, 0, 0, 0, 0, 1, 2], [0, 0, 0, 0, 0, 0, 1],
  [0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0],
];
const FRAME_MS = 110;
/** The loop waits this long after the pointer leaves, then fades its gain in over RAMP. */
const RESUME = 1200, RAMP = 400;
/** A painted dot at full, its four neighbours at this share. */
const SPLASH: readonly [number, number, number][] = [[0, 0, 1], [1, 0, 0.45], [-1, 0, 0.45], [0, 1, 0.45], [0, -1, 0.45]];

const lit = (f: number, r: number, c: number) => (LOOP[f][r] >> (N - 1 - c)) & 1;

export const mount: FigureMount = ({ stage, svg, read }, value) => {
  const bag = disposer();
  let tau = value, clock = 0, lastFrame = -1, leftAt = -1e9, painting = false;
  let prev: Vec2 | null = null;

  const C = Cam(45, 0.5, 2.12), ZB = -DROP - BT;
  fit(C, [[-BO, -BO, ZB], [EXT + BO, EXT + BO, ZB - 6], [EXT + BO, -BO, ZB], [-BO, EXT + BO, ZB], [0, 0, T]], 200, 160);
  const P = proj(C), front = facing(C);
  const g = mk("g", {}, svg);

  // base plate, its reflection, then the dashed drops, then the tile over them
  const [br, bi] = rings(-BO, -BO, EXT + BO, EXT + BO, 11, 1.8);
  reflect(svg, g, P, front, br, ZB, 12);
  put(solid(g), prism(P, front, br, bi, ZB, -DROP));
  const [tr, ti] = rings(0, 0, EXT, EXT, 7, 1.3);
  mk("path", { d: extremes(P, tr).map((q) => seg(P(q.u, q.v, 0), P(q.u, q.v, -DROP))).join(""), class: "nf dash" }, g);
  put(solid(g), prism(P, front, tr, ti, 0, T));
  mk("path", { d: poly(ringAt(P, rrect(3.5, 3.5, EXT - 3.5, EXT - 3.5, 4.5, 5), T)), class: "nf lo" }, g);

  const I = new Float32Array(N * N);
  const dots: SVGEllipseElement[] = [];
  for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) {
    const d = flatDot(g, C, R, "dot");
    place(d, P(M + c * PITCH, M + r * PITCH, T));
    dots.push(d);
  }

  /** Lights the cell nearest a point on the tile, and its neighbours less, never dimming what is brighter. */
  function excite(x: number, y: number, amt: number) {
    const c = Math.round((x - M) / PITCH), r = Math.round((y - M) / PITCH);
    for (const [dr, dc, k] of SPLASH) {
      const rr = r + dr, cc = c + dc;
      if (rr < 0 || rr >= N || cc < 0 || cc >= N) continue;
      I[rr * N + cc] = Math.max(I[rr * N + cc], amt * k);
    }
  }

  const B = register(stage, (dt, now) => {
    if (reducedMotion() && !painting) {
      // no loop: settle on a composed still, the ripple's widest ring
      for (let i = 0; i < N * N; i++) I[i] = Math.max(I[i] * Math.exp((-dt * 1000) / tau), lit(3, Math.floor(i / N), i % N) * 0.8);
    } else {
      const decay = Math.exp((-dt * 1000) / tau);
      for (let i = 0; i < N * N; i++) I[i] *= decay;
      const gain = painting ? 0 : clamp((now - leftAt - RESUME) / RAMP, 0, 1);
      if (gain > 0) {
        clock += dt * 1000;
        const f = Math.floor(clock / FRAME_MS) % LOOP.length;
        if (f !== lastFrame) {
          lastFrame = f;
          for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) if (lit(f, r, c)) I[r * N + c] = Math.max(I[r * N + c], gain);
        }
        read.textContent = `loop · ${String(f + 1).padStart(2, "0")}/${LOOP.length}`;
      } else read.textContent = painting ? "paint" : "afterglow";
    }
    for (let i = 0; i < N * N; i++) dots[i].setAttribute("opacity", (0.14 + 0.86 * clamp(I[i], 0, 1)).toFixed(3));
    return true;
  });
  bag.add(B.unregister);

  bag.add(pointer(stage, {
    move: (p) => {
      painting = true;
      const q = unproj(C, p[0], p[1], T);
      // fill in between moves, so a fast stroke leaves a line rather than dots
      if (prev) {
        const n = Math.ceil(Math.hypot(q[0] - prev[0], q[1] - prev[1]) / 3);
        for (let k = 1; k <= n; k++) excite(lerp(prev[0], q[0], k / n), lerp(prev[1], q[1], k / n), 1);
      } else excite(q[0], q[1], 1);
      prev = q;
      B.wake();
    },
    // the resume is a timestamp the tick reads, not a timer, so re-entering or tearing down has nothing to cancel
    leave: () => { painting = false; prev = null; leftAt = performance.now(); clock = 0; lastFrame = -1; B.wake(); },
  }));

  bag.add(() => svg.replaceChildren());
  return { set: (v) => { tau = v; }, destroy: bag.dispose };
};

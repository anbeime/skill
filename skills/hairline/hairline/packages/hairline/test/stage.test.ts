// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { frames, host, observers, pending, seen } from "./dom";
import { LAP, pointer, register, tour } from "../src/core/stage";
import { setReducedMotion } from "../src/core/motion";
import type { Vec2 } from "../src/core/iso";

describe("register", () => {
  it("two boards on one stage both see it, and both sleep and wake with it", () => {
    const el = host();
    const a = vi.fn(() => true), b = vi.fn(() => true);
    const ra = register(el, a), rb = register(el, b);
    frames(3);
    expect(a.mock.calls.length).toBeGreaterThan(1);
    expect(b.mock.calls.length).toBeGreaterThan(1);

    seen(el, false);
    const na = a.mock.calls.length, nb = b.mock.calls.length;
    frames(3);
    expect(a.mock.calls.length).toBe(na);
    expect(b.mock.calls.length).toBe(nb);

    seen(el, true);
    frames(3);
    expect(a.mock.calls.length).toBeGreaterThan(na);
    expect(b.mock.calls.length).toBeGreaterThan(nb);

    ra.unregister();
    rb.unregister();
    expect(pending()).toBe(0);
  });

  it("hands each tick performance.now(), even when the frame's own time trails it, as in a frame that loaded late", () => {
    const asked: Array<(t: number) => void> = [];
    vi.stubGlobal("requestAnimationFrame", (fn: (t: number) => void) => asked.push(fn));
    let clock = 5000;
    vi.spyOn(performance, "now").mockImplementation(() => clock);
    const seen: Array<[number, number]> = [], times: number[] = [];
    const r = register(host(), (dt, now) => { seen.push([dt, now]); return true; });
    for (let i = 0; i < 3; i++) {
      clock += 1000 / 60;
      times.push(clock);
      // Chrome's frame time in a late frame: seconds behind performance.now()
      asked.shift()!(clock - 4000);
    }
    expect(seen.slice(1).map(([, now]) => now)).toEqual(times);
    for (const [dt] of seen.slice(1)) expect(dt).toBeCloseTo(1 / 60);
    r.unregister();
  });

  it("watches the stage until its last board leaves", () => {
    const el = host(), other = host();
    const keep = register(other, () => false);
    const ra = register(el, () => false), rb = register(el, () => false);
    const o = [...observers][0];
    expect(o.targets.has(el)).toBe(true);
    ra.unregister();
    expect(o.targets.has(el)).toBe(true);
    rb.unregister();
    expect(o.targets.has(el)).toBe(false);
    keep.unregister();
  });

  it("a tick that throws sleeps alone: the error is reported, and every other board keeps its frames", () => {
    const thrown: Array<() => void> = [];
    vi.spyOn(globalThis, "setTimeout").mockImplementation(((fn: () => void) => { thrown.push(fn); return 0; }) as typeof setTimeout);
    const el = host(), other = host();
    const boom = new Error("boom");
    let n = 0;
    const bad = register(el, () => { if (n++ > 0) throw boom; return true; });
    const good = vi.fn(() => true), ok = register(other, good);
    expect(() => frames(5)).not.toThrow();
    expect(n).toBe(2);
    expect(good.mock.calls.length).toBeGreaterThanOrEqual(6);
    expect(pending()).toBe(1);
    expect(thrown).toHaveLength(1);
    expect(thrown[0]).toThrow(boom);
    bad.unregister();
    ok.unregister();
  });
});

type Call = { kind: "move" | "leave"; type: string; p?: Vec2 };
/** A figure's side of the seam: handlers that log every call, through pointer() as a figure's would. */
function stub(el: HTMLElement) {
  const log: Call[] = [];
  const off = pointer(el, {
    move: (p, e) => { log.push({ kind: "move", type: e.pointerType, p: [p[0], p[1]] }); },
    leave: (e) => { log.push({ kind: "leave", type: e.pointerType }); },
  });
  return { log, off };
}
/** Runs frames until `fn` holds, at most `cap` of them; returns whether it holds. */
const until = (fn: () => boolean, cap: number) => { for (let n = 0; n < cap && !fn(); n++) frames(); return fn(); };
const mouse = (el: Element, type: string, x = 50, y = 50) =>
  el.dispatchEvent(new PointerEvent(type, { pointerType: "mouse", pointerId: 1, bubbles: true, clientX: x, clientY: y }));
const tick = () => new Promise((done) => setTimeout(done, 5));

describe("tour", () => {
  afterEach(() => setReducedMotion(false));

  it("walks the stops: enters from the edge, arrives, leaves at null, and loops", () => {
    const el = host(), { log } = stub(el), stops: number[] = [];
    const h = tour(el, [[200, 100], null], (i) => stops.push(i));
    expect(until(() => log.length > 0, 200)).toBe(true);
    /* the ray from the centre through [200, 100] meets the top edge at [200, 0]: the first move is just inside it */
    expect(log[0].type).toBe("ghost");
    expect(log[0].p![0]).toBeCloseTo(200, 0);
    expect(log[0].p![1]).toBeLessThan(20);
    expect(until(() => stops.length === 1, 60)).toBe(true);
    expect(log.at(-1)!.p![0]).toBeCloseTo(200, 0);
    expect(log.at(-1)!.p![1]).toBeCloseTo(100, 0);
    expect(until(() => stops.length === 2, 80)).toBe(true);
    expect(log.at(-1)).toMatchObject({ kind: "leave", type: "ghost" });
    const n = log.length;
    expect(until(() => log.length > n, 120)).toBe(true);
    expect(log[n].p![1]).toBeLessThan(20);
    expect(stops).toEqual([0, 1]);
    h.stop();
  });

  it("a real pointer takes the handlers; after it leaves, the ghost waits and starts the lap again from the edge", async () => {
    const el = host(), { log } = stub(el), stops: number[] = [];
    const h = tour(el, [[200, 100], [300, 160], null], (i) => stops.push(i));
    expect(until(() => stops.length === 1, 240)).toBe(true);
    mouse(el, "pointermove");
    expect(log.at(-1)).toMatchObject({ kind: "move", type: "mouse", p: [50, 50] });
    const n = log.length;
    frames(200);
    expect(log.length).toBe(n);
    mouse(el, "pointerleave");
    await tick();
    expect(log.at(-1)).toMatchObject({ kind: "leave", type: "mouse" });
    frames(60);
    expect(log.length).toBe(n + 1);
    expect(until(() => log.length > n + 1, 30)).toBe(true);
    expect(log.at(-1)).toMatchObject({ kind: "move", type: "ghost" });
    expect(log.at(-1)!.p![1]).toBeLessThan(20);
    expect(until(() => stops.length === 2, 60)).toBe(true);
    expect(stops).toEqual([0, 0]);
    h.stop();
  });

  it("a leave with no pointer before it does not restart the lap", async () => {
    const el = host(), { log } = stub(el), stops: number[] = [];
    const h = tour(el, [[200, 100], null], (i) => stops.push(i));
    expect(until(() => log.length > 10, 200)).toBe(true);
    mouse(el, "pointerleave");
    await tick();
    const n = log.length;
    frames(1);
    expect(log.length).toBe(n + 1);
    expect(log.at(-1)!.type).toBe("ghost");
    h.stop();
  });

  it("focus inside the stage holds it, and a hand that leaves while the keyboard is inside does not free it", async () => {
    const el = host(), { log } = stub(el);
    const btn = document.createElement("button");
    el.append(btn);
    const h = tour(el, [[200, 100], null]);
    expect(until(() => log.length > 0, 200)).toBe(true);
    btn.focus();
    const n = log.length;
    frames(300);
    expect(log.length).toBe(n);
    mouse(el, "pointermove");
    mouse(el, "pointerleave");
    await tick();
    expect(log.slice(n).map((c) => c.type)).toEqual(["mouse", "mouse"]);
    const m = log.length;
    frames(300);
    expect(log.length).toBe(m);
    btn.blur();
    expect(until(() => log.length > m, 100)).toBe(true);
    expect(log.at(-1)).toMatchObject({ kind: "move", type: "ghost" });
    h.stop();
  });

  it("under reduced motion the ghost leaves and rests; woken when the preference clears, it goes on", () => {
    const el = host(), { log } = stub(el);
    const h = tour(el, [[200, 100], null]);
    expect(until(() => log.length > 3, 200)).toBe(true);
    setReducedMotion(true);
    frames(2);
    expect(log.at(-1)).toMatchObject({ kind: "leave", type: "ghost" });
    const n = log.length;
    frames(200);
    expect(log.length).toBe(n);
    setReducedMotion(false);
    seen(el, true); // what the media-query listener does on a change: every board wakes
    expect(until(() => log.length > n, 200)).toBe(true);
    expect(log.at(-1)!.type).toBe("ghost");
    h.stop();
  });

  it("offscreen it sleeps where it is, and goes on from there when seen", () => {
    const el = host(), { log } = stub(el);
    const h = tour(el, [[200, 100], null]);
    expect(until(() => log.length > 5, 200)).toBe(true);
    const last = log.at(-1)!.p!;
    seen(el, false);
    const n = log.length;
    frames(200);
    expect(log.length).toBe(n);
    seen(el, true);
    frames(1);
    expect(log.length).toBe(n + 1);
    expect(Math.hypot(log[n].p![0] - last[0], log[n].p![1] - last[1])).toBeLessThan(30);
    h.stop();
  });

  it("stop() leaves the stage and forgets the tour; a hand after it is just a hand", () => {
    const el = host(), { log } = stub(el);
    const h = tour(el, [[200, 100], null]);
    expect(until(() => log.length > 0, 200)).toBe(true);
    h.stop();
    expect(log.at(-1)).toMatchObject({ kind: "leave", type: "ghost" });
    const n = log.length;
    frames(300);
    expect(log.length).toBe(n);
    expect(pending()).toBe(0);
    mouse(el, "pointermove");
    h.stop();
    expect(log.at(-1)).toMatchObject({ kind: "move", type: "mouse" });
  });

  it("three stages start at three different times", () => {
    const set = [0, 1, 2].map(() => { const el = host(); return { log: stub(el).log, h: tour(el, LAP), first: -1 }; });
    for (let f = 0; f < 200; f++) {
      frames();
      for (const s of set) if (s.first < 0 && s.log.length) s.first = f;
    }
    expect(set.every((s) => s.first >= 0)).toBe(true);
    expect(new Set(set.map((s) => s.first)).size).toBe(3);
    for (const s of set) s.h.stop();
  });

  it("an empty tour does nothing, and a tour started before the figure's pointer() waits for it", () => {
    const el = host(), { log } = stub(el);
    const none = tour(el, []);
    frames(300);
    expect(log.length).toBe(0);
    none.stop();

    const late = host();
    const h = tour(late, [[200, 100], null]);
    frames(200);
    const { log: l2 } = stub(late);
    expect(until(() => l2.length > 0, 5)).toBe(true);
    expect(l2[0].type).toBe("ghost");
    h.stop();
  });

  it("a move that throws under the ghost stops that tour alone: the error is reported, and the other figures keep their frames", () => {
    const thrown: Array<() => void> = [];
    vi.spyOn(globalThis, "setTimeout").mockImplementation(((fn: () => void) => { thrown.push(fn); return 0; }) as typeof setTimeout);
    const el = host(), other = host();
    const boom = new Error("boom");
    let moves = 0;
    pointer(el, { move: () => { moves++; throw boom; }, leave: () => {} });
    const h = tour(el, [[200, 100], null]);
    const good = vi.fn(() => true), ok = register(other, good);
    expect(() => until(() => moves > 0, 200)).not.toThrow();
    expect(moves).toBe(1);
    expect(thrown).toHaveLength(1);
    expect(thrown[0]).toThrow(boom);
    const n = good.mock.calls.length;
    frames(10);
    expect(good.mock.calls.length).toBe(n + 10);
    expect(pending()).toBe(1);
    /* a board registered afterwards is ticked by the loop too, not only at register */
    const late = vi.fn(() => true), l = register(host(), late);
    frames(3);
    expect(late.mock.calls.length).toBe(4);
    expect(moves).toBe(1);
    l.unregister();
    ok.unregister();
    h.stop();
  });

  it("the disposer forgets the handlers, and a new pointer() takes over", () => {
    const el = host(), a = stub(el);
    const h = tour(el, [[200, 100], null]);
    expect(until(() => a.log.length > 0, 200)).toBe(true);
    a.off();
    const n = a.log.length;
    frames(50);
    expect(a.log.length).toBe(n);
    const b = stub(el);
    expect(until(() => b.log.length > 0, 5)).toBe(true);
    expect(b.log[0].type).toBe("ghost");
    h.stop();
    expect(b.log.at(-1)).toMatchObject({ kind: "leave", type: "ghost" });
  });
});

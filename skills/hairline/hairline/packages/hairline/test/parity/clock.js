/**
 * A virtual clock for tests. Add it to a page with context.addInitScript,
 * before any of the page's own scripts.
 *
 * Live until window.__freeze(at): nothing changes in behaviour. From the
 * freeze on, performance.now() reads `at` and time moves only when
 * window.__advance(ms) is called: due timers fire in order, the rAF queue is
 * flushed with the new timestamp, and every animation in the document, CSS
 * transitions included, is paused and seeked to where the virtual clock says
 * it is. Same calls, same drawing.
 */
(() => {
  const realNow = performance.now.bind(performance);
  const realDateNow = Date.now;
  const realRAF = window.requestAnimationFrame.bind(window);
  const realCAF = window.cancelAnimationFrame.bind(window);
  const realST = window.setTimeout.bind(window);
  const realCT = window.clearTimeout.bind(window);
  const realSI = window.setInterval.bind(window);
  const realCI = window.clearInterval.bind(window);

  let frozen = false;
  let now = 0;
  let dateOffset = 0;
  let seq = 1e9; // virtual ids never collide with the browser's
  let rafs = new Map();
  const timers = new Map();
  const started = new WeakMap();
  const rethrow = (e) => queueMicrotask(() => { throw e; });

  performance.now = () => (frozen ? now : realNow());
  Date.now = () => (frozen ? Math.round(now + dateOffset) : realDateNow());

  window.requestAnimationFrame = (cb) => {
    if (!frozen) return realRAF(cb);
    const id = ++seq; rafs.set(id, cb); return id;
  };
  window.cancelAnimationFrame = (id) => { if (!rafs.delete(id)) realCAF(id); };
  window.setTimeout = (cb, ms = 0, ...args) => {
    if (!frozen) return realST(cb, ms, ...args);
    const id = ++seq; timers.set(id, { at: now + Math.max(0, ms), cb, args, every: 0 }); return id;
  };
  window.clearTimeout = (id) => { if (!timers.delete(id)) realCT(id); };
  window.setInterval = (cb, ms = 0, ...args) => {
    if (!frozen) return realSI(cb, ms, ...args);
    const every = Math.max(1, ms);
    const id = ++seq; timers.set(id, { at: now + every, cb, args, every }); return id;
  };
  window.clearInterval = (id) => { if (!timers.delete(id)) realCI(id); };

  function runTimers(until) {
    for (;;) {
      let next = null, nextId = 0;
      for (const [id, t] of timers) if (t.at <= until && (!next || t.at < next.at)) { next = t; nextId = id; }
      if (!next) return;
      now = next.at;
      if (next.every) next.at += next.every; else timers.delete(nextId);
      try { if (typeof next.cb === "function") next.cb(...next.args); } catch (e) { rethrow(e); }
    }
  }

  /* At the freeze, an animation keeps the time it has already played: an
     entrance that finished on the wall clock stays finished (fill keeps it
     listed). After it, one first seen starts now, whatever the wall clock ran
     it for in between: an input between two advances starts transitions live */
  function seekAnimations(keepPlayed) {
    for (const a of document.getAnimations()) {
      if (!started.has(a)) { started.set(a, now - (keepPlayed ? Number(a.currentTime) || 0 : 0)); a.pause(); }
      const t = now - started.get(a);
      const end = a.effect ? a.effect.getComputedTiming().endTime : 0;
      if (Number.isFinite(end) && t >= end) { a.finish(); continue; }
      a.currentTime = t;
    }
  }

  window.__realTimeout = realST;
  window.__now = () => (frozen ? now : realNow());
  window.__freeze = (at) => {
    if (frozen) return;
    now = at ?? realNow();
    dateOffset = realDateNow() - now;
    frozen = true;
    seekAnimations(true);
  };
  window.__advance = (ms) => {
    if (!frozen) throw new Error("__advance before __freeze");
    const target = now + Math.max(0, ms);
    runTimers(target);
    now = target;
    const due = rafs; rafs = new Map();
    for (const cb of due.values()) { try { cb(now); } catch (e) { rethrow(e); } }
    seekAnimations(false);
    return now;
  };
})();

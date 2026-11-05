/**
 * Plays a script against a figure, whoever is hosting it. `target` is the
 * host's side of it:
 *   stage  the element the pointer acts on (a Playwright Locator)
 *   snap() the svg's markup and the caption, read from the page
 *   set()  changes the figure's option to the script's value
 * Time only moves here, through window.__advance (clock.js).
 *
 * The pointer is dispatched, not a real mouse: a real one reports whole
 * pixels, so the same viewBox point would land differently on stages of
 * different widths. A dispatched event carries the exact point.
 */
export const FRAME = 1000 / 60;

/** Mask and gradient ids count up per page; number them by first appearance instead. */
export function normalise(svg) {
  const seen = new Map();
  return svg.replace(/hl-fd\d+/g, (id) => {
    if (!seen.has(id)) seen.set(id, `fd${seen.size + 1}`);
    return seen.get(id);
  });
}

const fire = (stage, type, pt) => stage.evaluate((el, [type, pt]) => {
  const r = el.getBoundingClientRect();
  el.dispatchEvent(new PointerEvent(type, {
    pointerType: "mouse", pointerId: 1, bubbles: type !== "pointerleave",
    clientX: pt ? r.left + (pt[0] / 400) * r.width : r.left - 40,
    clientY: pt ? r.top + (pt[1] / 320) * r.height : r.top - 40,
  }));
}, [type, pt]);

export async function play(page, target, steps) {
  const out = [];
  for (const s of steps) {
    if (s.adv) await page.evaluate(([n, f]) => { for (let i = 0; i < n; i++) window.__advance(f); }, [s.adv, FRAME]);
    else if (s.move) await fire(target.stage, "pointermove", s.move);
    else if (s.out) await fire(target.stage, "pointerleave", null);
    else if (s.focus) await target.stage.focus();
    else if (s.key) await page.keyboard.press(s.key);
    else if (s.set) await target.set();
    else if (s.cp) { const { svg, read } = await target.snap(); out.push({ at: s.cp, read, svg: normalise(svg) }); }
    else throw new Error(`unknown step ${JSON.stringify(s)}`);
  }
  return out;
}

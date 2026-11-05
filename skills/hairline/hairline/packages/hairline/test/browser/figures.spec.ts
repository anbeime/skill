import { expect, test, type Page } from "@playwright/test";

/** The figures in a real browser: input, focus, reduced motion, shadow roots, a clean console. */

const IDS = ["riffle", "terrain", "exploded", "phosphor", "slow", "turntable", "keyboard", "elevator", "phone", "laptop", "terminal", "cabinet", "branches", "vault", "lockers", "padlock", "patch", "dish", "router", "loupe", "sieve", "rail", "plug", "query", "drawer", "basket", "plot", "hub", "relay", "settle", "format", "rebuild", "stack"] as const;
type Id = (typeof IDS)[number];

const mount = (page: Page, id: Id, options: Record<string, unknown> = {}) =>
  page.evaluate(([id, options]) => { window.__hl.mount(id, options); }, [id, options] as const);
const read = (page: Page) => page.evaluate(() => window.__hl.read());
/** A pointer event at a point of the 400 × 320 viewBox; no point is a leave. */
const fire = (page: Page, type: string, pt?: [number, number]) => page.locator("#host").evaluate((el, [type, pt]) => {
  const r = el.getBoundingClientRect();
  el.dispatchEvent(new PointerEvent(type, {
    pointerType: "mouse", pointerId: 1, bubbles: type !== "pointerleave",
    clientX: pt ? r.left + (pt[0] / 400) * r.width : r.left - 40,
    clientY: pt ? r.top + (pt[1] / 320) * r.height : r.top - 40,
  }));
}, [type, pt] as const);

test.beforeEach(async ({ page }) => { await page.goto("/"); });

test("every figure mounts, answers the pointer and leaves, with nothing on the console", async ({ page }) => {
  const problems: string[] = [];
  page.on("pageerror", (e) => problems.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") problems.push(m.text()); });
  for (const id of IDS) {
    await mount(page, id);
    const host = page.locator("#host");
    await expect(host.locator("svg > *").first()).toBeAttached();
    const box = (await host.boundingBox())!;
    expect(box.width / box.height).toBeCloseTo(5 / 4, 2);
    await host.hover({ position: { x: box.width * 0.45, y: box.height * 0.5 } });
    await page.mouse.move(box.x + box.width * 0.6, box.y + box.height * 0.45, { steps: 6 });
    await page.waitForTimeout(150);
    await page.mouse.move(2, 2);
    await page.evaluate(() => window.__hl.figure!.destroy());
    expect(await host.evaluate((el) => el.outerHTML)).toBe('<div id="host"></div>');
  }
  expect(problems).toEqual([]);
});

test("Riffle walks its cards from the keyboard and says each one in the live region", async ({ page }) => {
  await mount(page, "riffle");
  const host = page.locator("#host"), live = host.locator("[data-hairline-live]");
  await page.keyboard.press("Tab");
  await expect(host).toBeFocused();
  await page.keyboard.press("ArrowLeft");
  await expect(live).toHaveText("01");
  await page.keyboard.press("ArrowRight");
  await expect(live).toHaveText("02");
  await page.keyboard.press("ArrowRight");
  await expect(live).toHaveText("03");
  await page.keyboard.press("Escape");
  await expect(live).toHaveText("rest");
  await page.keyboard.press("ArrowLeft");
  await host.blur();
  await expect(live).toHaveText("rest");
  /* read, not seen */
  const box = (await live.boundingBox())!;
  expect(box.width).toBeLessThanOrEqual(1);
  expect(box.height).toBeLessThanOrEqual(1);
});

test("Turntable settles on a quarter turn after a flick", async ({ page }) => {
  await mount(page, "turntable");
  expect(await read(page)).toBe("az 045° · el 30°");
  for (const x of [50, 120, 200, 280, 350]) { await fire(page, "pointermove", [x, 176]); await page.waitForTimeout(16); }
  await fire(page, "pointerleave");
  /* still coasting, the platter shows a quarter turn for a frame as it passes one: wait for a read-out that holds */
  const held = async () => { const was = await read(page); await page.waitForTimeout(150); return (await read(page)) === was ? was : "turning"; };
  await expect.poll(held, { timeout: 8000 }).toMatch(/^az (045|135|225|315)° · el 30°$/);
  const settled = await read(page);
  await page.waitForTimeout(400);
  expect(await read(page)).toBe(settled);
  expect(await page.evaluate(() => window.__hl.reads.length)).toBeGreaterThan(3);
});

test("under reduced motion the loops hold still", async ({ browser }) => {
  const context = await browser.newContext({ reducedMotion: "reduce" });
  const page = await context.newPage();
  await page.goto("/");
  for (const id of ["phosphor", "slow"] as const) {
    await mount(page, id);
    await page.waitForTimeout(700);
    const a = await page.locator("#host > svg").innerHTML();
    await page.waitForTimeout(500);
    expect(await page.locator("#host > svg").innerHTML(), id).toBe(a);
  }
  await context.close();
});

test("a figure in a shadow root is styled there, and only there", async ({ page }) => {
  const fill = await page.evaluate(() => {
    const outer = document.createElement("div");
    document.body.append(outer);
    const root = outer.attachShadow({ mode: "open" });
    const el = document.createElement("div");
    el.style.width = "400px";
    root.append(el);
    window.__hl.mount("terrain", { theme: "dark" }, el);
    return {
      fill: getComputedStyle(el.querySelector("svg .sil")!).fill,
      position: getComputedStyle(el).position,
      inShadow: root.adoptedStyleSheets.length,
      inDocument: document.adoptedStyleSheets.length + document.querySelectorAll("style[data-hairline-style]").length,
    };
  });
  expect(fill).toEqual({ fill: "rgb(8, 9, 10)", position: "relative", inShadow: 1, inDocument: 0 });
});

// Review Focus 5: frameworks build a node first and attach it afterwards
test("a figure mounted on a detached element is drawn and styled once attached", async ({ page }) => {
  const result = await page.evaluate(async () => {
    const el = document.createElement("div");
    el.style.width = "400px";
    window.__hl.mount("slow", {}, el);
    const before = el.querySelector("svg")!.childElementCount;
    document.body.append(el);
    await new Promise((done) => setTimeout(done, 300));
    const first = el.querySelector("svg")!.innerHTML;
    await new Promise((done) => setTimeout(done, 300));
    return {
      before: before > 0,
      box: [el.offsetWidth, el.offsetHeight],
      fill: getComputedStyle(el.querySelector("svg .sil")!).fill,
      running: el.querySelector("svg")!.innerHTML !== first,
    };
  });
  expect(result).toEqual({ before: true, box: [400, 320], fill: "rgb(255, 255, 255)", running: true });
});

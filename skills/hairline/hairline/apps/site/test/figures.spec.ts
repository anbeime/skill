import { expect, test, type Page } from "@playwright/test";

const SHELVES = ["Interfaces", "Data", "Machines", "Devices", "Coding", "Security", "Connectivity", "Empty", "Marks"];

function watch(page: Page): string[] {
  const noise: string[] = [];
  page.on("console", (m) => {
    // Vercel Analytics' script exists only on Vercel
    if (m.location().url.includes("/_vercel/")) return;
    if (m.type() === "error" || m.type() === "warning") noise.push(`${m.type()}: ${m.text()}`);
  });
  page.on("pageerror", (e) => noise.push(`pageerror: ${e}`));
  return noise;
}

const tiles = (page: Page) => page.locator(".fig-tile");
const shelf = (page: Page, name: string) => page.locator(".shelves .shelf", { hasText: name });

test("/figures prerenders thirty-three empty boxes among thirty-six tiles, then draws them with a clean console", async ({ page, request }) => {
  const html = await (await request.get("/figures")).text();
  expect(html.match(/<div style="aspect-ratio:5 \/ 4"><\/div>/g)).toHaveLength(33);
  expect(html.match(/class="fig-tile"/g)).toHaveLength(36);
  expect(html).not.toContain("data-planned");

  const noise = watch(page);
  await page.goto("/figures");
  await expect(tiles(page)).toHaveCount(36);
  await expect(page.locator(".fig-tile [data-hairline] > svg")).toHaveCount(33);
  await expect(page.locator(".fig-tile .fig-ghost, .fig-tile[data-planned]")).toHaveCount(0);
  await expect(page.locator("h1")).toHaveText("Every figure, by what it draws.");
  await expect(page.locator(".doc-section h2")).toHaveText(SHELVES);
  await expect(page.locator(".fig-name").first()).toHaveAccessibleName("Exploded");
  expect(noise).toEqual([]);
});

test("the shelves filter: All is pressed at first, a shelf shows only itself and names itself in the address", async ({ page }) => {
  await page.goto("/figures");
  await expect(shelf(page, "All")).toHaveAttribute("aria-pressed", "true");
  await expect(page.locator(".shelves .shelf-n")).toHaveText(["36", "1", "3", "3", "3", "6", "3", "6", "8", "3"]);

  await shelf(page, "Machines").click();
  await expect(shelf(page, "Machines")).toHaveAttribute("aria-pressed", "true");
  await expect(shelf(page, "All")).toHaveAttribute("aria-pressed", "false");
  await expect(page.locator(".doc-section h2")).toHaveText(["Machines"]);
  await expect(tiles(page)).toHaveCount(3);
  await expect(page.locator(".fig-tile [data-hairline] > svg")).toHaveCount(3);
  expect(new URL(page.url()).hash).toBe("#machines");
  // the plate sits under the pressed row
  await expect.poll(() => page.evaluate(() => {
    const plate = document.querySelector(".shelf-plate")!.getBoundingClientRect();
    const row = document.querySelector('.shelf[aria-pressed="true"]')!.getBoundingClientRect();
    return Math.abs(plate.top - row.top);
  })).toBeLessThan(1);

  await shelf(page, "All").click();
  await expect(tiles(page)).toHaveCount(36);
  expect(new URL(page.url()).hash).toBe("");
});

test("a link to a shelf opens on it, without scrolling", async ({ page }) => {
  await page.goto("/figures#security");
  await expect(page.locator(".doc-section h2")).toHaveText(["Security"]);
  await expect(shelf(page, "Security")).toHaveAttribute("aria-pressed", "true");
  expect(await page.evaluate(() => window.scrollY)).toBe(0);
});

test("the shelves' marks sit on the name in the top bar, and the shelves start where the docs' column does", async ({ page }) => {
  for (const width of [1100, 1280, 1600]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/figures");
    const at = await page.evaluate(() => {
      const left = (el: Element | null) => el!.getBoundingClientRect().left;
      return { mark: left(document.querySelector(".shelves .shelf svg")), name: left(document.querySelector(".topbar-name")), h1: left(document.querySelector("h1")) };
    });
    expect(Math.abs(at.mark - at.name), `${width}`).toBeLessThan(0.5);
    expect(Math.abs(at.h1 - at.name - 260), `${width}`).toBeLessThan(0.5);
  }
  await page.goto("/docs");
  const docs = await page.evaluate(() => document.querySelector("h1")!.getBoundingClientRect().left);
  await page.goto("/figures");
  expect(await page.evaluate(() => document.querySelector("h1")!.getBoundingClientRect().left)).toBeCloseTo(docs, 0);
});

test("picking a figure opens the drawer: the figure large, the slider, what it reads, its code; Escape closes it", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  const noise = watch(page);
  await page.goto("/figures");
  const drawer = page.locator("#figure-drawer");
  await expect(drawer).not.toHaveAttribute("data-open");

  const name = page.locator(".fig-name", { hasText: "Terrain" });
  await page.locator(".fig-tile", { has: name }).locator(".fig-stage").click();
  await expect(drawer).toHaveAttribute("data-open", "");
  await expect(name).toHaveAttribute("aria-expanded", "true");
  await expect(drawer.locator("h2")).toHaveText("Terrain");
  await expect(drawer.locator(".detail-shelf")).toHaveText("Data");
  await expect(drawer.locator(".detail-close")).toBeFocused();
  await expect(drawer.locator("[data-hairline] > svg")).toHaveCount(1);
  await expect(drawer.locator(".detail-sum")).toContainText("Higher intensity: A wider area rises.");
  await expect(drawer.locator(".detail-reads b")).not.toBeEmpty();

  const slider = drawer.locator('input[type="range"]');
  await slider.fill("0.9");
  await expect(drawer.locator(".slider")).toContainText("0.90");

  await expect(drawer.locator("[role=tab]")).toHaveText(["React", "Vanilla", "CDN"]);
  await expect(drawer.locator(".code-body")).toContainText('import { Terrain } from "@lucasmarkes/hairline/react"');
  await drawer.locator("[role=tab]", { hasText: "Vanilla" }).click();
  await expect(drawer.locator(".code-body")).toContainText("terrain(document.getElementById");
  await drawer.locator(".icopy").click();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain('import { terrain } from "@lucasmarkes/hairline"');

  await page.keyboard.press("Escape");
  await expect(drawer).not.toHaveAttribute("data-open");
  await expect(name).toBeFocused();
  await expect(name).toHaveAttribute("aria-expanded", "false");
  // the contents go once it is out of sight
  await expect(drawer.locator(".detail")).toHaveCount(0);
  expect(noise).toEqual([]);
});

test("closing the drawer returns focus to the tile's button, with its ring for the keyboard alone", async ({ page }) => {
  await page.goto("/figures");
  const drawer = page.locator("#figure-drawer");
  const name = page.locator(".fig-name", { hasText: "Keyboard" });
  const stage = page.locator(".fig-tile", { has: name }).locator(".fig-stage");
  const ringed = () => name.evaluate((el) => el.matches(":focus-visible"));
  const outline = () => name.evaluate((el) => getComputedStyle(el).outlineStyle === "none" || parseFloat(getComputedStyle(el).outlineWidth) === 0 ? "none" : "drawn");

  // the mouse opened it: neither the × nor Escape brings the ring back with focus
  for (const shut of [() => drawer.locator(".detail-close").click(), () => page.keyboard.press("Escape")]) {
    await stage.click();
    await expect(drawer).toHaveAttribute("data-open");
    await shut();
    await expect(drawer).not.toHaveAttribute("data-open");
    await expect(name).toBeFocused();
    expect(await ringed()).toBe(false);
    expect(await outline()).toBe("none");
  }

  // the keyboard opened it, or took over inside it with Tab: Escape returns focus with its ring
  for (const open of [async () => { await name.focus(); await page.keyboard.press("Enter"); }, async () => { await stage.click(); await page.keyboard.press("Tab"); }]) {
    await open();
    await expect(drawer).toHaveAttribute("data-open");
    await page.keyboard.press("Escape");
    await expect(drawer).not.toHaveAttribute("data-open");
    await expect(name).toBeFocused();
    expect(await ringed()).toBe(true);
    expect(await outline()).toBe("drawn");
  }
});

test("opening the drawer focuses its ×, with its ring for the keyboard alone", async ({ page }) => {
  await page.goto("/figures");
  const drawer = page.locator("#figure-drawer");
  const close = drawer.locator(".detail-close");
  const name = page.locator(".fig-name", { hasText: "Keyboard" });
  const stage = page.locator(".fig-tile", { has: name }).locator(".fig-stage");
  const ringed = () => close.evaluate((el) => el.matches(":focus-visible"));

  for (const open of [() => stage.click(), () => name.click()]) {
    await open();
    await expect(drawer).toHaveAttribute("data-open");
    await expect(close).toBeFocused();
    expect(await ringed()).toBe(false);
    await close.click();
    await expect(drawer).not.toHaveAttribute("data-open");
  }

  // opened by the keyboard, shut by Escape or by the × pressed with Enter, focus goes back to the name with its ring
  for (const [key, shut] of [["Enter", "Escape"], [" ", "Enter"]]) {
    await name.focus();
    await page.keyboard.press(key);
    await expect(drawer).toHaveAttribute("data-open");
    await expect(close).toBeFocused();
    expect(await ringed()).toBe(true);
    await page.keyboard.press(shut);
    await expect(drawer).not.toHaveAttribute("data-open");
    await expect(name).toBeFocused();
    expect(await name.evaluate((el) => el.matches(":focus-visible"))).toBe(true);
  }
});

test("on a phone the shelves are a strip under the top bar, and nothing scrolls sideways", async ({ page }) => {
  for (const width of [414, 390, 360, 320]) {
    await page.setViewportSize({ width, height: 800 });
    await page.goto("/figures");
    await expect(page.locator(".shelves")).toBeHidden();
    await expect(page.locator(".figs-pill")).toHaveCount(10);
    expect(await page.evaluate(() => document.documentElement.scrollWidth), `${width}`).toBeLessThanOrEqual(width);
    // the top bar's links stay inside it
    const right = await page.evaluate(() => document.querySelector(".topbar nav")!.getBoundingClientRect().right);
    expect(right).toBeLessThanOrEqual(width);
    // with Figures first, the name still stands clear of the links: the version goes under 400px
    const names = await page.evaluate(() => {
      const text = (el: Element) => { const r = document.createRange(); r.selectNodeContents(el); return r.getBoundingClientRect(); };
      return text(document.querySelector(".topbar nav > a")!).left - text(document.querySelector(".topbar-name")!).right;
    });
    expect(names, `${width}`).toBeGreaterThanOrEqual(20);

    await page.locator(".figs-pill", { hasText: "Connectivity" }).click();
    await expect(page.locator(".doc-section h2")).toHaveText(["Connectivity"]);
    expect(new URL(page.url()).hash).toBe("#connectivity");
    await page.locator(".fig-name", { hasText: "Dish" }).click();
    const box = await page.locator("#figure-drawer").boundingBox();
    expect(box!.x).toBe(0);
    expect(box!.width).toBe(width);
  }
});

test("the Marks shelf shows three figures the skill made, each with its prompt and no install code", async ({ page }) => {
  await page.goto("/figures#marks");
  const shelf = page.locator("#shelf-marks");
  await expect(shelf.locator(".fig-tile")).toHaveCount(3);
  await expect(shelf).toContainText("not affiliated");
  const tile = shelf.locator(".fig-tile").first();
  const frame = tile.frameLocator("iframe");
  await expect(frame.locator("#stage svg > *").first()).toBeAttached();
  await expect(frame.locator(".controls")).toBeHidden();
  // the page's ground is clear, so the tile's ring, under the frame, shows
  await expect(frame.locator("body")).toHaveCSS("background-color", "rgba(0, 0, 0, 0)");
  await tile.getByRole("button", { name: "Vercel" }).click();
  const drawer = page.locator("#figure-drawer");
  await expect(drawer).toContainText("/hairline-create an empty state for");
  await expect(drawer).toContainText("not affiliated");
  await expect(drawer.getByRole("tab")).toHaveCount(0);
  await expect(drawer.locator("input[type=range]")).toHaveCount(0);
  await expect(drawer.getByRole("link", { name: "hairline-create" })).toHaveAttribute("href", "/skills");
});

test("Escape pressed inside a made page's frame closes the drawer, as it does outside", async ({ page }) => {
  await page.goto("/figures#marks");
  const name = page.locator("#shelf-marks").getByRole("button", { name: "Vercel" });
  await name.click();
  const drawer = page.locator("#figure-drawer");
  await expect(drawer).toHaveAttribute("data-open", "");
  // the page's own slider, in the drawer's frame, takes the keys
  const slider = drawer.frameLocator("iframe").locator("#intensity");
  await slider.focus();
  await expect(slider).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(drawer).not.toHaveAttribute("data-open");
  await expect(name).toBeFocused();
});

// Review Focus 4: a page that does not load leaves the tile its box
test("a made tile keeps its box when its page is missing", async ({ page }) => {
  await page.route("**/skill/hairline-mastra.html*", (route) => route.fulfill({ status: 404, body: "" }));
  await page.goto("/figures#marks");
  // the hash is read after mount and the shelves are built again for it: measure the frame that stays
  await expect(page.locator('.shelf[data-filter="marks"]')).toHaveAttribute("aria-pressed", "true");
  const box = (await page.locator("#shelf-marks .fig-tile").nth(1).locator("iframe.made-frame").boundingBox())!;
  expect(box.width / box.height).toBeCloseTo(5 / 4, 1);
});

// a made page paints its controls before the tile can hide them: the frame shows nothing until it shows only the stage
test("a made tile never shows its page's controls while the page loads", async ({ page }) => {
  let release!: () => void;
  const held = new Promise<void>((done) => (release = done));
  await page.route("**/skill/hairline-vercel.html*", async (route) => {
    await held;
    await route.continue();
  });
  await page.goto("/figures#marks");
  const frame = page.locator("#shelf-marks .fig-tile").first().locator("iframe.made-frame");
  await expect(frame).toHaveCSS("opacity", "0");
  release();
  await expect(frame).toHaveAttribute("data-quiet", "");
  await expect(frame).toHaveCSS("opacity", "1");
  await expect(frame.contentFrame().locator(".controls")).toBeHidden();
});

const terrainStage = (page: Page) => tiles(page).filter({ has: page.locator(".fig-name", { hasText: "Terrain" }) }).locator(".fig-stage svg").first();

test("a tile walks its figure with no hand on the page", async ({ page }) => {
  const noise = watch(page);
  await page.goto("/figures");
  /* no hand on the page: the pointer is parked in the corner, off every tile */
  await page.mouse.move(0, 0);
  const svg = terrainStage(page);
  await expect(svg).toBeVisible();
  const first = await svg.innerHTML();
  await expect.poll(() => svg.innerHTML(), { timeout: 15000 }).not.toBe(first);
  expect(noise).toEqual([]);
});

test("under reduced motion a tile rests", async ({ page }) => {
  const noise = watch(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/figures");
  const svg = terrainStage(page);
  await expect(svg).toBeVisible();
  const first = await svg.innerHTML();
  await page.waitForTimeout(4000);
  expect(await svg.innerHTML()).toBe(first);
  expect(noise).toEqual([]);
});

import { expect, test, type Page } from "@playwright/test";

/**
 * The palette rules, in the order the stylesheet applies them: the `theme`
 * option, an ancestor that says dark, the page's color-scheme, light. Read
 * off a real computed style: the plate colour a silhouette is filled with.
 */
const LIGHT = "rgb(255, 255, 255)", DARK = "rgb(8, 9, 10)";

const plate = (page: Page) => page.evaluate(() => getComputedStyle(document.querySelector("#host svg .sil")!).fill);
const mount = (page: Page, options: Record<string, unknown> = {}) =>
  page.evaluate((options) => { window.__hl.mount("terrain", options); }, options);

test.beforeEach(async ({ page }) => { await page.goto("/"); });

test("light when nothing says otherwise", async ({ page }) => {
  await mount(page);
  expect(await plate(page)).toBe(LIGHT);
});

test("follows the page's color-scheme", async ({ page }) => {
  await mount(page);
  await page.evaluate(() => { document.documentElement.style.colorScheme = "dark"; });
  expect(await plate(page)).toBe(DARK);
  await page.evaluate(() => { document.documentElement.style.colorScheme = "light dark"; });
  expect(await plate(page)).toBe(LIGHT);
  await page.emulateMedia({ colorScheme: "dark" });
  expect(await plate(page)).toBe(DARK);
});

test("an ancestor with class dark or data-theme=dark wins over the color-scheme", async ({ page }) => {
  await mount(page);
  await page.evaluate(() => { document.documentElement.style.colorScheme = "light"; document.body.className = "dark"; });
  expect(await plate(page)).toBe(DARK);
  await page.evaluate(() => { document.body.className = ""; document.documentElement.dataset.theme = "dark"; });
  expect(await plate(page)).toBe(DARK);
});

test("the theme option wins over both", async ({ page }) => {
  await page.evaluate(() => { document.body.className = "dark"; document.documentElement.style.colorScheme = "dark"; });
  await mount(page, { theme: "light" });
  expect(await plate(page)).toBe(LIGHT);
  await page.evaluate(() => window.__hl.figure!.update({ theme: "dark" }));
  await page.evaluate(() => { document.body.className = ""; document.documentElement.style.colorScheme = "light"; });
  expect(await plate(page)).toBe(DARK);
  await page.evaluate(() => window.__hl.figure!.update({ theme: "auto" }));
  expect(await plate(page)).toBe(LIGHT);
});

test("a --hairline-* property wins over every palette, and a page rule over the stylesheet", async ({ page }) => {
  await mount(page, { theme: "dark" });
  await page.addStyleTag({ content: "#host { --hairline-plate: rgb(1, 2, 3); --hairline-stroke: 2; } [data-hairline] { aspect-ratio: 1; }" });
  expect(await plate(page)).toBe("rgb(1, 2, 3)");
  expect(await page.evaluate(() => getComputedStyle(document.querySelector("#host svg .sil")!).strokeWidth)).toBe("2px");
  const box = (await page.locator("#host").boundingBox())!;
  expect(box.width).toBe(box.height);
});

test("without constructable stylesheets it falls back to a style element", async ({ context, page }) => {
  await context.addInitScript(() => { delete (Document.prototype as { adoptedStyleSheets?: unknown }).adoptedStyleSheets; });
  await page.goto("/");
  await mount(page, { theme: "dark" });
  await mount(page, { theme: "dark" });
  expect(await page.locator("style[data-hairline-style]").count()).toBe(1);
  expect(await plate(page)).toBe(DARK);
});

test("without light-dark() it stays light under a dark color-scheme, and the class still works", async ({ context, page }) => {
  await context.addInitScript(() => {
    const supports = CSS.supports.bind(CSS);
    CSS.supports = ((a: string, b?: string) => (String(b ?? a).includes("light-dark") ? false : b === undefined ? supports(a) : supports(a, b))) as typeof CSS.supports;
  });
  await page.goto("/");
  await mount(page);
  await page.evaluate(() => { document.documentElement.style.colorScheme = "dark"; });
  expect(await plate(page)).toBe(LIGHT);
  await page.evaluate(() => { document.body.className = "dark"; });
  expect(await plate(page)).toBe(DARK);
});

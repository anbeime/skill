import { expect, test, type Page } from "@playwright/test";

const IDS = ["riffle", "terrain", "exploded", "phosphor", "slow", "turntable", "keyboard", "elevator", "phone", "laptop", "terminal", "cabinet", "branches", "vault", "lockers", "padlock", "patch", "dish", "router", "loupe", "sieve", "rail", "plug", "query", "drawer", "basket", "plot", "hub", "relay", "settle", "format", "rebuild", "stack"];
const MANAGERS = [
  ["npm", "npm i @lucasmarkes/hairline"],
  ["pnpm", "pnpm add @lucasmarkes/hairline"],
  ["yarn", "yarn add @lucasmarkes/hairline"],
  ["bun", "bun add @lucasmarkes/hairline"],
  // the build's base URL, which is localhost:3000 off Vercel
  ["shadcn", "npx shadcn@latest add http://localhost:3000/r/hairline.json"],
] as const;

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

test("the home prerenders the drawing's empty box, then draws it with a clean console", async ({ page, request }) => {
  const html = await (await request.get("/")).text();
  // the drawing's box is empty on the server, and no figure is on the home
  expect(html.match(/<div class="assembly" data-assembly="true"><\/div>/g)).toHaveLength(1);
  expect(html).not.toContain("data-hairline");

  const noise = watch(page);
  await page.goto("/");
  await expect(page.locator("[data-assembly] > svg")).toHaveCount(1);
  await expect(page.locator("[data-install]").first()).toHaveText(/npm i @lucasmarkes\/hairline/);
  await expect(page.locator("[data-version]")).toHaveText(/^v\d+\.\d+\.\d+/);
  expect(noise).toEqual([]);
});

test("the top bar holds the name with the version beside it, then the figures, the skills, the docs, the story and GitHub, and no llms.txt button", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".topbar nav > *")).toHaveCount(5);
  await expect(page.locator(".topbar nav > a").nth(0)).toHaveText("Figures");
  await expect(page.locator(".topbar nav > a").nth(1)).toHaveText("Skills");
  await expect(page.locator(".topbar nav > a").nth(2)).toHaveText("Docs");
  await expect(page.locator(".topbar nav [data-version]")).toHaveCount(0);
  await expect(page.locator(".topbar")).not.toContainText("llms.txt");
  // the version follows the name on its baseline, a step smaller, close enough to read as one
  const [name, version] = await Promise.all([".topbar-name", "[data-version]"].map((s) => page.locator(s).evaluate((el) => {
    const r = document.createRange();
    r.selectNodeContents(el);
    const box = r.getBoundingClientRect();
    return { left: box.left, right: box.right, bottom: box.bottom, size: parseFloat(getComputedStyle(el).fontSize) };
  })));
  const gap = version.left - name.right;
  expect(gap).toBeGreaterThan(4);
  expect(gap).toBeLessThan(12);
  expect(Math.abs(version.bottom - name.bottom)).toBeLessThan(2.5);
  expect(version.size).toBeLessThan(name.size);
});

test("the top bar's links sit as one row: one height, one centre line, one type, even spaces between them", async ({ page }) => {
  await page.goto("/");
  const items = await page.locator(".topbar nav > *").evaluateAll((els) => els.map((el) => {
    const box = el.getBoundingClientRect();
    const range = document.createRange();
    range.selectNodeContents(el);
    // what the eye reads as the item: its text, or its icon
    const ink = (el.querySelector("svg") ?? range).getBoundingClientRect();
    const style = getComputedStyle(el);
    return { height: box.height, middle: box.top + box.height / 2, left: ink.left, right: ink.right, type: [style.fontSize, style.fontWeight, style.color, style.backgroundColor].join(" ") };
  }));
  expect(items).toHaveLength(5);
  expect(new Set(items.map((i) => i.height)).size).toBe(1);
  for (const i of items) expect(Math.abs(i.middle - items[0].middle)).toBeLessThan(0.5);
  expect(new Set(items.map((i) => i.type)).size).toBe(1);
  const spaces = items.slice(1).map((i, n) => i.left - items[n].right);
  for (const s of spaces) expect(Math.abs(s - spaces[0])).toBeLessThan(1.5);
});

test("the docs prerender an empty box per figure, then draw one figure per row with a clean console", async ({ page, request }) => {
  const html = await (await request.get("/docs")).text();
  expect(html.match(/<div style="aspect-ratio:5 \/ 4"><\/div>/g)).toHaveLength(IDS.length);
  // the empty state's figure is the one more, at its own width
  expect(html.match(/<div style="aspect-ratio:5 \/ 4;width:200px"><\/div>/g)).toHaveLength(1);
  expect(html).not.toMatch(/aspect-ratio:5 \/ 4[^"]*"[^>]*><svg/);

  const noise = watch(page);
  await page.goto("/docs");
  await expect(page.locator("[data-hairline] > svg")).toHaveCount(IDS.length + 1);
  for (const id of IDS) await expect(page.locator(`[data-row="${id}"] [data-hairline] > svg > *`).first()).toBeAttached();
  await expect(page.locator("[data-size]")).toHaveText(/^\d+\.\d kB$/);
  expect(noise).toEqual([]);
});

test("the empty-states section draws its snippet live: a sieve at 200px over a heading and a button, then the code", async ({ page }) => {
  await page.goto("/docs");
  const section = page.locator("#empty-states");
  const demo = section.locator("[data-empty]");
  const figure = demo.locator("[data-hairline]");
  await expect(figure.locator("> svg > *").first()).toBeAttached();
  await expect(figure).toHaveAttribute("aria-label", /empty sieve/i);
  expect((await figure.boundingBox())!.width).toBeCloseTo(200, 0);
  await expect(demo.getByRole("heading", { level: 3 })).toHaveText("No results match these filters");
  await expect(demo.getByRole("button", { name: "Clear filters" })).toBeVisible();
  // the live block comes first, the code after it, and the code says the same words
  const code = section.locator("pre");
  expect((await demo.boundingBox())!.y).toBeLessThan((await code.boundingBox())!.y);
  await expect(code).toContainText('<Sieve style={{ width: 200 }} label="An empty sieve" />');
  await expect(code).toContainText("<h2>No results match these filters</h2>");
  await expect(code).toContainText("Clear filters</button>");
});

test("the docs' code is in greys: every token's colour has equal red, green and blue", async ({ page }) => {
  await page.goto("/docs");
  const colours = await page.locator("main pre span").evaluateAll((spans) => spans.map((s) => getComputedStyle(s).color));
  // eight blocks of highlighted code, some two hundred spans: a page that lost its highlighting falls far short
  expect(colours.length).toBeGreaterThan(150);
  const tinted = colours.filter((c) => {
    const [r, g, b] = c.match(/\d+(\.\d+)?/g)!.map(Number);
    return !(r === g && g === b);
  });
  expect(tinted).toEqual([]);
});

/** Waits for every transition and entrance on the page to finish. */
const settled = (page: Page) =>
  expect.poll(() => page.evaluate(() => document.getAnimations().filter((a) => a.playState === "running").length)).toBe(0);

test("the home's entrance settles within 1.4s, with its hero blocks 70ms apart", async ({ page }) => {
  await page.goto("/");
  const timing = await page.evaluate(() => {
    const of = (el: Element) => el.getAnimations().map((a) => a.effect!.getComputedTiming());
    const hero = [...document.querySelectorAll(".hero-rise > *")].map((el) => Math.min(...of(el).map((t) => Number(t.delay))));
    const end = Math.max(...[...document.querySelectorAll(".hero-rise > *")].flatMap((el) => of(el).map((t) => Number(t.endTime))));
    return { gaps: hero.slice(1).map((d, n) => d - hero[n]), end };
  });
  expect(timing.gaps).toEqual([70, 70, 70, 70]);
  expect(timing.end).toBeLessThanOrEqual(1400);
});

/** What the drawing shows now: each path's shape and how much of it is drawn, in order. */
const drawing = (page: Page) =>
  page.locator("[data-assembly] svg").evaluate((svg) => [...svg.querySelectorAll("path")].map((p) => `${p.getAttribute("d")} ${p.style.strokeDashoffset} ${p.style.opacity}`).join("\n"));

test("the drawing builds the window in three plates, each adding its stage, then breathes", async ({ page }) => {
  await page.goto("/");
  const svg = page.locator("[data-assembly] svg");
  // three plates; the frame's two lines on each, the blocks' nine on the upper two, the details' six on the top one
  await expect(svg.locator(":scope > g:not([mask])")).toHaveCount(3);
  await expect(svg.locator(".part, .lit")).toHaveCount(2 * 3 + 9 * 2 + 6);
  // the last line drawn is the top plate's lit row: once it is in full, the whole window is
  const lit = svg.locator(".lit");
  await expect.poll(() => lit.evaluate((el: SVGPathElement) => Number(el.style.strokeDashoffset)), { timeout: 8000 }).toBe(0);
  // every part and every rule is drawn in full
  const undrawn = () => svg.evaluate((el) => [...el.querySelectorAll<SVGPathElement>(".part, .lit, .rule")].filter((p) => p.style.opacity !== "1" || Number(p.style.strokeDashoffset) !== 0).length);
  expect(await undrawn()).toBe(0);
  // at rest the stack keeps moving, slowly
  const before = await drawing(page);
  await page.waitForTimeout(400);
  expect(await drawing(page)).not.toBe(before);
});

test("under reduced motion the drawing is at rest at once, and holds still", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await expect(page.locator("[data-assembly] .lit")).toHaveCSS("stroke-dashoffset", "0px");
  const before = await drawing(page);
  await page.waitForTimeout(500);
  expect(await drawing(page)).toBe(before);
});

test("the drawing never moves the page: its box is the same height before it mounts and after it is built", async ({ browser }) => {
  for (const width of [1440, 390, 320]) {
    const viewport = { width, height: 800 };
    const height = (page: Page) => page.evaluate(() => `${document.documentElement.scrollHeight} ${Math.round(document.querySelector(".assembly")!.getBoundingClientRect().height)}`);
    const off = await browser.newContext({ viewport, javaScriptEnabled: false });
    const bare = await off.newPage();
    await bare.goto("/");
    const prerendered = await height(bare);
    await off.close();
    const on = await browser.newContext({ viewport, reducedMotion: "reduce" });
    const page = await on.newPage();
    await page.goto("/");
    await expect(page.locator("[data-assembly] > svg")).toHaveCount(1);
    expect(await height(page), `${width}px`).toBe(prerendered);
    await on.close();
  }
});

test("the command and Get started are one height, and on a wide screen they share a line", async ({ page }) => {
  for (const width of [1200, 320]) {
    await page.setViewportSize({ width, height: 800 });
    await page.goto("/");
    // the row has risen into place, so both are read where they come to rest
    await settled(page);
    const pill = (await page.locator(".hero-get .pill").boundingBox())!;
    const button = (await page.locator(".hero-get").getByRole("link", { name: "Get started" }).boundingBox())!;
    expect(pill.height, `${width}px`).toBe(36);
    expect(button.height, `${width}px`).toBe(36);
    if (width === 1200) expect(pill.y).toBeCloseTo(button.y, 0);
  }
});

test("a hero button's text holds still through a press: no jump when its layer comes and goes", async ({ page }) => {
  await page.goto("/");
  await settled(page);
  // the press is what is watched; following the link would end the recording
  await page.evaluate(() => document.addEventListener("click", (e) => e.preventDefault(), true));
  for (const name of ["Get started"]) {
    const button = page.locator(".hero-get").getByRole("link", { name });
    const box = (await button.boundingBox())!;
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.waitForTimeout(100);
    // what the compositor draws, frame by frame, which a screenshot would redraw from scratch
    const cdp = await page.context().newCDPSession(page);
    const frames: { at: number; data: string }[] = [];
    cdp.on("Page.screencastFrame", (f) => {
      frames.push({ at: Date.now(), data: f.data });
      cdp.send("Page.screencastFrameAck", { sessionId: f.sessionId }).catch(() => {});
    });
    await cdp.send("Page.startScreencast", { format: "png" });
    await page.mouse.down();
    await page.waitForTimeout(400);
    await page.mouse.up();
    const up = Date.now();
    await page.waitForTimeout(600);
    await cdp.send("Page.stopScreencast");
    await cdp.detach();
    const viewport = page.viewportSize()!.width;
    // the release eases out, so its last frame moves the text least; a jump there is the text being redrawn
    const release = frames.filter((f) => f.at > up).map((f) => f.data);
    expect(release.length).toBeGreaterThan(2);
    const worst = await page.evaluate(async ({ frames, box, viewport }) => {
      const text = async (data: string) => {
        const bitmap = await createImageBitmap(await (await fetch(`data:image/png;base64,${data}`)).blob());
        const s = bitmap.width / viewport;
        const [x, y, w, h] = [box.x + 12, box.y + 8, box.width - 24, box.height - 16].map((v) => Math.round(v * s));
        const canvas = new OffscreenCanvas(w, h);
        canvas.getContext("2d")!.drawImage(bitmap, x, y, w, h, 0, 0, w, h);
        return canvas.getContext("2d")!.getImageData(0, 0, w, h).data;
      };
      const [before, after] = await Promise.all(frames.map(text));
      let worst = 0;
      for (let k = 0; k < before.length; k += 4) worst = Math.max(worst, Math.abs(before[k] - after[k]));
      return worst;
    }, { frames: release.slice(-2), box, viewport });
    expect(worst, String(name)).toBeLessThan(64);
  }
});

test("the install pill copies every manager's command", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/");
  const pill = page.locator("[data-install]").first();
  for (const [label, code] of MANAGERS) {
    await expect(pill).toHaveAttribute("data-install", label);
    await expect(pill.locator("code")).toHaveText(code);
    const copy = pill.getByRole("button", { name: "Copy install command" });
    await copy.click();
    await expect(copy).toHaveAttribute("data-copied", "true");
    await expect(pill.getByText("Copied")).toBeAttached();
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(code);
    await pill.getByRole("button", { name: new RegExp(`\\(${label}\\): switch to`) }).click();
  }
  await expect(pill).toHaveAttribute("data-install", "npm");
});

test("a second copy keeps Copied up for its own full time, not what was left of the first", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.clock.install();
  await page.goto("/");
  // from here time moves only when the test moves it: on a slow machine the real time between steps would add to it
  await page.clock.pauseAt(await page.evaluate(() => Date.now() + 1000));
  const pill = page.locator("[data-install]").first();
  const copy = pill.getByRole("button", { name: "Copy install command" });
  await copy.click();
  await expect(copy).toHaveAttribute("data-copied", "true");
  await page.clock.runFor(1000);
  await pill.getByRole("button", { name: /\(npm\): switch to/ }).click();
  await copy.click();
  // the second copy has landed once the clipboard holds its command
  await expect.poll(() => page.evaluate(() => navigator.clipboard.readText())).toBe(MANAGERS[1][1]);
  await page.clock.runFor(1000);
  await expect(pill.getByText("Copied")).toBeAttached();
  await page.clock.runFor(700);
  await expect(copy).not.toHaveAttribute("data-copied");
});

test("without a clipboard, copy selects the text instead and throws nothing", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", { value: { writeText: () => Promise.reject(new DOMException("denied", "NotAllowedError")) } });
  });
  const noise = watch(page);
  await page.goto("/");
  const pill = page.locator("[data-install]").first();
  const copy = pill.getByRole("button", { name: "Copy install command" });
  await copy.click();
  await expect(copy).not.toHaveAttribute("data-copied");
  expect(await page.evaluate(() => window.getSelection()?.toString())).toBe("npm i @lucasmarkes/hairline");
  expect(noise).toEqual([]);
});

test("Get started leads to the docs, whose quick start pastes three ways and copies the tab on show", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/");
  await page.getByRole("link", { name: "Get started" }).click();
  await expect(page).toHaveURL(/\/docs$/);
  const quick = page.locator("#quick-start");
  await expect(quick.getByRole("tab")).toHaveText(["React", "Vanilla", "CDN"]);
  await expect(quick.locator(".code-title")).toHaveText("app/page.tsx");
  await quick.getByRole("tab", { name: "CDN" }).click();
  await expect(quick.locator(".code-title")).toHaveText("index.html");
  await expect(quick.getByRole("tabpanel")).toContainText("https://esm.sh/@lucasmarkes/hairline");
  await quick.getByRole("button", { name: "Copy code" }).click();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toMatch(/^<div id="figure"/);
  await expect(page.locator("#options [data-options] tbody tr td:first-child")).toHaveText(["intensity", "theme", "label", "onRead", "play"]);
});

test("llms.txt and the registry item are served", async ({ request }) => {
  const llms = await request.get("/llms.txt");
  expect(llms.headers()["content-type"]).toContain("text/plain");
  expect(await llms.text()).toContain("# hairline");

  const item = await (await request.get("/r/hairline.json")).json();
  expect(item.name).toBe("hairline");
  expect(item.dependencies).toEqual(["@lucasmarkes/hairline"]);
  expect(item.files[0].path).toBe("components/ui/hairline.tsx");
  expect(item.files[0].content).toContain('"use client"');
});

// the build's base URL, which is localhost:3000 off Vercel
const BASE = "http://localhost:3000";

test("a pasted link shows the page it leads to: each page's card has its own title, text and address", async ({ request }) => {
  const CARDS = [
    ["/", "hairline", /^Thirty-three isometric line figures/],
    ["/figures", "Figures", /^Eight shelves, thirty-three figures, grouped by what they draw/],
    ["/docs", "Docs", /^Thirty-three isometric line figures/],
    ["/skills", "Make your own figure", /^Two skills for coding agents/],
    ["/inspo", "How Hairline was made", /^A long brief/],
  ] as const;
  for (const [path, title, text] of CARDS) {
    const html = await (await request.get(path)).text();
    const tag = (key: string) => html.match(new RegExp(`<meta (?:property|name)="${key}" content="([^"]*)"`))?.[1];
    // Open Graph's tags and X's say the same thing
    for (const key of ["og:title", "twitter:title"]) expect(tag(key), `${path} ${key}`).toBe(title);
    for (const key of ["og:description", "twitter:description"]) expect(tag(key), `${path} ${key}`).toMatch(text);
    for (const key of ["og:image", "twitter:image"]) expect(tag(key), `${path} ${key}`).toBe(`${BASE}/og.png`);
    expect(tag("og:url"), path).toBe(path === "/" ? BASE : BASE + path);
    expect(tag("twitter:card"), path).toBe("summary_large_image");
    // the account the footer links
    expect(tag("twitter:creator"), path).toBe("@lucasmarkes__");
  }
});

test("robots.txt lets every crawler in and names the sitemap, which lists the five pages", async ({ request }) => {
  const robots = await (await request.get("/robots.txt")).text();
  expect(robots).toMatch(/^User-Agent: \*\nAllow: \/\n/);
  expect(robots).toContain(`Sitemap: ${BASE}/sitemap.xml`);

  const sitemap = await (await request.get("/sitemap.xml")).text();
  expect([...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1])).toEqual([BASE, `${BASE}/figures`, `${BASE}/docs`, `${BASE}/skills`, `${BASE}/inspo`]);
});

test("the page fits a phone, with the longest install command, and its buttons", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 800 });
  await page.goto("/");
  const width = () => page.evaluate(() => document.documentElement.scrollWidth);
  expect(await width()).toBeLessThanOrEqual(390);

  const pill = page.locator("[data-install]").first();
  for (let i = 0; i < 4; i++) await pill.getByRole("button", { name: /: switch to/ }).click();
  await expect(pill).toHaveAttribute("data-install", "shadcn");
  expect(await width()).toBeLessThanOrEqual(390);

  const controls = page.locator(".hero-get .btn");
  await expect(controls).toHaveCount(1);
  for (const control of await controls.all()) {
    const box = (await control.boundingBox())!;
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(390);
  }
  // the drawing keeps to the column, its floor fading out before the edge
  const art = (await page.locator("[data-assembly]").boundingBox())!;
  expect(art.x).toBeGreaterThanOrEqual(0);
  expect(art.x + art.width).toBeLessThanOrEqual(390);
});

/** Every element that holds text of its own, outside code, the hero's serif word and the figures, with its family. */
const families = (page: Page) =>
  page.evaluate(() =>
    [...document.querySelectorAll("body *")]
      // the install pill is code, prompt and all
      .filter((el) => !el.closest("h1 em, code, pre, .pill, [data-hairline]") && [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent!.trim()))
      .map((el) => `${el.tagName} ${getComputedStyle(el).fontFamily}`),
  );

test("one family outside the hero: the serif is the headline's one word, mono is code", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("h1 em")).toHaveCSS("font-family", /Instrument Serif/);
  const home = await families(page);
  expect(home.length).toBeGreaterThan(5);
  expect(home.filter((f) => !/geist/i.test(f) || /mono/i.test(f))).toEqual([]);

  await page.goto("/docs");
  const docs = await families(page);
  expect(docs.length).toBeGreaterThan(40);
  expect(docs.filter((f) => !/geist/i.test(f) || /mono/i.test(f))).toEqual([]);
  for (const id of IDS) await expect(page.locator(`[data-row="${id}"] h3`)).toHaveCSS("font-style", "normal");
});

test("a command wider than the pill fades at the edge until it is scrolled to its end, and shows itself whole on hover", async ({ page }) => {
  await page.setViewportSize({ width: 1200, height: 800 });
  await page.goto("/");
  const pill = page.locator("[data-install]").first();
  const line = pill.locator("code");
  await expect(line).not.toHaveAttribute("data-more");
  await expect(line).toHaveCSS("mask-image", "none");

  for (let i = 0; i < 4; i++) await pill.getByRole("button", { name: /: switch to/ }).click();
  const [, shadcn] = MANAGERS[4];
  await expect(line).toHaveAttribute("title", shadcn);
  await expect(line).toHaveAttribute("data-more", "");
  await expect(line).toHaveCSS("mask-image", /gradient/);

  await line.evaluate((el) => el.scrollTo({ left: el.scrollWidth }));
  await expect(line).not.toHaveAttribute("data-more");
  await expect(line).toHaveCSS("mask-image", "none");
});

test("the footer links the author's site, then X, GitHub, npm and llms.txt", async ({ page }) => {
  await page.goto("/");
  const footer = page.locator("footer");
  await expect(footer.getByRole("link", { name: "Lucas Marques" })).toHaveAttribute("href", "https://lucasmarkes.com");
  await expect(footer.getByRole("link", { name: "X", exact: true })).toHaveAttribute("href", "https://x.com/lucasmarkes__");
  await expect(footer.getByRole("link")).toHaveText(["Lucas Marques", "X", "GitHub", "npm", "llms.txt"]);
});

test("a code block copies its code without the line numbers, and a signature has none", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/docs");
  const blocks = page.locator("#react [data-code]");
  await expect(blocks.locator(".code-title")).toHaveText(["Signature", "app/page.tsx"]);
  const usage = blocks.last();
  await usage.getByRole("button", { name: "Copy code" }).click();
  const text = await page.evaluate(() => navigator.clipboard.readText());
  expect(text.split("\n")[0]).toBe('import { Terrain } from "@lucasmarkes/hairline/react";');
  expect(text).not.toMatch(/^\s*\d/m);
  const number = (block: typeof usage) => block.locator(".line").first().evaluate((el) => getComputedStyle(el, "::before").content);
  expect(await number(usage)).not.toBe("none");
  expect(await number(blocks.first())).toBe("none");
});

test("the quick start remembers the tab a reader picked", async ({ page }) => {
  await page.goto("/docs");
  const quick = page.locator("#quick-start");
  await quick.getByRole("tab", { name: "Vanilla" }).click();
  await page.reload();
  await expect(quick.getByRole("tab", { name: "Vanilla" })).toHaveAttribute("aria-selected", "true");
  await expect(quick.locator(".code-title")).toHaveText("main.ts");
});

test("when storage throws, the quick start stays on React and still switches, with a clean console", async ({ page }) => {
  await page.addInitScript(() => {
    Object.defineProperty(window, "localStorage", { get() { throw new DOMException("blocked", "SecurityError"); } });
  });
  const noise = watch(page);
  await page.goto("/docs");
  const quick = page.locator("#quick-start");
  await expect(quick.getByRole("tab", { name: "React" })).toHaveAttribute("aria-selected", "true");
  await quick.getByRole("tab", { name: "CDN" }).click();
  await expect(quick.getByRole("tab", { name: "CDN" })).toHaveAttribute("aria-selected", "true");
  expect(noise).toEqual([]);
});

test("the docs fit a phone down to 320px: rows stack text first, and wide code and tables scroll in their own box", async ({ page }) => {
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 800 });
    await page.goto("/docs");
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    const row = page.locator('[data-row="terrain"]');
    // the whole text block, so a tile centred beside a short heading does not pass for stacked
    const text = (await row.locator(":scope > div").first().boundingBox())!;
    const tile = (await row.locator(".tile").boundingBox())!;
    expect(tile.y).toBeGreaterThan(text.y + text.height);
  }
});

test("the figures' link goes to the figures page", async ({ page }) => {
  await page.goto("/docs");
  await page.getByRole("link", { name: "Try each one on the figures page →" }).click();
  await expect(page).toHaveURL(/\/figures$/);
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Every figure");
});

test("the sidebar's links land on their section under the top bar and mark it, and scrolling moves the mark", async ({ page }) => {
  await page.goto("/docs");
  const nav = page.getByRole("navigation", { name: "Docs" });
  await expect(nav.getByRole("link")).toHaveText(["Install", "Quick start", "Options", "Empty states", "React", "Vanilla", "CDN", "Figures", "Theme", "Accessibility"]);
  await expect(nav.getByRole("link", { name: "Install" })).toHaveAttribute("aria-current", "location");

  await nav.getByRole("link", { name: "Theme" }).click();
  await expect(page).toHaveURL(/\/docs#theme$/);
  await expect(nav.getByRole("link", { name: "Theme" })).toHaveAttribute("aria-current", "location");
  await expect(nav.locator("[aria-current]")).toHaveCount(1);
  await expect.poll(() => page.locator("#theme-title").evaluate((el) => el.getBoundingClientRect().top)).toBeGreaterThanOrEqual(54);

  await page.evaluate(() => document.getElementById("figures")!.scrollIntoView());
  await expect(nav.getByRole("link", { name: "Figures" })).toHaveAttribute("aria-current", "location");

  // Accessibility is too short to reach the band; the end of the page marks it
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await expect(nav.getByRole("link", { name: "Accessibility" })).toHaveAttribute("aria-current", "location");
});

test("opening /docs#theme lands on Theme, clear of the top bar, with Theme marked", async ({ page }) => {
  await page.goto("/docs#theme");
  const nav = page.getByRole("navigation", { name: "Docs" });
  await expect(nav.getByRole("link", { name: "Theme" })).toHaveAttribute("aria-current", "location");
  const top = await page.locator("#theme-title").evaluate((el) => el.getBoundingClientRect().top);
  expect(top).toBeGreaterThanOrEqual(54);
  expect(top).toBeLessThan(200);
});

test("on a phone the sidebar is one strip under the top bar, and it follows the reader", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 800 });
  await page.goto("/docs");
  const strip = page.locator(".doc-strip");
  const scroller = strip.locator(".doc-strip-scroll");
  await expect(strip).toBeVisible();
  await expect(page.locator(".doc-sidebar")).toBeHidden();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await expect(scroller).toHaveAttribute("data-end");
  await expect(scroller).not.toHaveAttribute("data-start");

  const inside = async (name: string) => {
    const s = (await scroller.boundingBox())!;
    const b = (await strip.getByRole("link", { name }).boundingBox())!;
    return b.x >= s.x - 1 && b.x + b.width <= s.x + s.width + 1;
  };
  // the page moves, not the strip: the strip has to bring Accessibility in by itself
  await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
  await expect(strip.getByRole("link", { name: "Accessibility" })).toHaveAttribute("aria-current", "location");
  await expect.poll(() => inside("Accessibility")).toBe(true);
  await expect(scroller).toHaveAttribute("data-start");

  await strip.getByRole("link", { name: "Install" }).click();
  await expect(page).toHaveURL(/#install$/);
  await expect(strip.getByRole("link", { name: "Install" })).toHaveAttribute("aria-current", "location");
  await expect.poll(() => inside("Install")).toBe(true);
  // the heading clears the top bar and the strip
  await expect.poll(async () => {
    const s = (await strip.boundingBox())!;
    const t = (await page.locator("#install-title").boundingBox())!;
    return t.y >= s.y + s.height;
  }).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});

test("the sidebar draws the line to its section in its group's colour, and only that group stays lit", async ({ page }) => {
  await page.goto("/docs");
  const nav = page.locator(".doc-sidebar");
  await nav.getByRole("link", { name: "Theme" }).click();
  await expect(nav.getByRole("link", { name: "Theme" })).toHaveAttribute("aria-current", "location");
  const read = () => nav.evaluate((nav) => {
    const style = (el: Element, pseudo?: string) => getComputedStyle(el, pseudo);
    const on = nav.querySelector("a[aria-current]")!;
    const off = nav.querySelector("a:not([aria-current])")!;
    const group = on.closest(".rail-group")!;
    const other = nav.querySelector(".rail-group:not(:has([aria-current]))")!;
    const scale = (ul: Element) => {
      const after = style(ul, "::after");
      const bottom = after.clipPath.match(/^inset\(\S+ \S+ ([^\s)]+)/)?.[1] ?? "0px";
      return 1 - (bottom.endsWith("%") ? parseFloat(bottom) / 100 : parseFloat(bottom) / parseFloat(after.height));
    };
    return {
      // the trunk reaches into the marked group alone, and one arm is drawn: the marked row's
      reach: [...nav.querySelectorAll("ul")].map((ul) => scale(ul) > 0),
      arms: [...nav.querySelectorAll("li")].filter((li) => style(li, "::after").clipPath === "inset(0px)").map((li) => li.textContent),
      tip: [style(on, "::before").transform, style(on, "::before").backgroundColor, style(off, "::before").transform],
      on: style(on).color,
      off: style(off).color,
      lit: [style(group.querySelector(".rail-title")!).color, style(group.querySelector("svg")!).filter],
      dim: [style(other.querySelector(".rail-title")!).color, style(other.querySelector("svg")!).filter],
      dots: nav.querySelectorAll(".doc-dot").length,
    };
  });
  // the line has finished drawing: the arm is out and the tip has landed
  await expect.poll(async () => {
    const r = await read();
    return [r.arms, r.tip[0]];
  }).toEqual([["Theme"], "none"]);
  const r = await read();
  expect(r.reach).toEqual([false, false, true]);
  // the tip is in Reference's amber; the unmarked rows have none
  expect(r.tip.slice(1)).toEqual(["rgb(245, 158, 11)", "matrix(0, 0, 0, 0, 0, 0)"]);
  expect(r.on).toBe("rgb(10, 10, 10)");
  expect(r.off).toBe("rgb(115, 115, 115)");
  expect(r.lit).toEqual(["rgb(10, 10, 10)", "none"]);
  expect(r.dim).toEqual(["rgb(82, 82, 82)", "grayscale(1)"]);
  expect(r.dots).toBe(0);
});

test("the line draws from section to section instead of jumping, and under reduced motion it jumps", async ({ page }) => {
  await page.goto("/docs");
  const nav = page.locator(".doc-sidebar");
  await expect(nav.getByRole("link", { name: "Install" })).toHaveAttribute("aria-current", "location");
  // Reference's trunk, as it reaches down to Theme
  const flight = () => nav.evaluate((nav) => new Promise<number[]>((done) => {
    const ul = nav.querySelectorAll("ul")[2];
    const ys: number[] = [];
    const t0 = performance.now();
    const tick = () => {
      // the trunk is a border uncovered from the top: its reach is what the clip-path's bottom inset leaves
      const after = getComputedStyle(ul, "::after");
      const bottom = after.clipPath.match(/^inset\(\S+ \S+ ([^\s)]+)/)?.[1] ?? "0px";
      ys.push(1 - (bottom.endsWith("%") ? parseFloat(bottom) / 100 : parseFloat(bottom) / parseFloat(after.height)));
      if (performance.now() - t0 < 700) requestAnimationFrame(tick);
      else done(ys);
    };
    requestAnimationFrame(tick);
    // straight to Theme: no section passes through the band on the way, so the mark moves once
    document.getElementById("theme")!.scrollIntoView({ behavior: "instant" });
  }));
  const ys = await flight();
  const to = ys[ys.length - 1];
  expect(to).toBeGreaterThan(0.25);
  expect(ys.filter((y) => y > 0.02 && y < to - 0.02).length).toBeGreaterThanOrEqual(3);

  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await expect(nav.getByRole("link", { name: "Install" })).toHaveAttribute("aria-current", "location");
  await page.waitForTimeout(800);
  const jump = await flight();
  expect(jump.filter((y) => y > 0.02 && y < to - 0.02)).toEqual([]);
});

test("a deep link marks only its own section, with no other marked first", async ({ page }) => {
  await page.addInitScript(() => {
    const seen: string[] = [];
    (window as unknown as { seen: string[] }).seen = seen;
    const note = (el: Element) => el.matches(".doc-sidebar a[aria-current]") && seen.push(el.textContent!);
    new MutationObserver((records) => {
      for (const r of records) {
        if (r.type === "attributes") note(r.target as Element);
        for (const n of r.addedNodes) if (n instanceof Element) [n, ...n.querySelectorAll("*")].forEach(note);
      }
    }).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ["aria-current"] });
  });
  await page.goto("/docs#theme");
  const nav = page.locator(".doc-sidebar");
  await expect(nav.getByRole("link", { name: "Theme" })).toHaveAttribute("aria-current", "location");
  expect([...new Set(await page.evaluate(() => (window as unknown as { seen: string[] }).seen))]).toEqual(["Theme"]);
});

test("on a tall screen, a click on a section near the end marks that section, not the last", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1600 });
  await page.goto("/docs");
  const nav = page.locator(".doc-sidebar");
  await nav.getByRole("link", { name: "Theme" }).click();
  // the page cannot scroll Theme up to the top bar: it stops at its end, with Theme in view
  await expect.poll(() => page.evaluate(() => innerHeight + scrollY >= document.documentElement.scrollHeight - 2)).toBe(true);
  await page.waitForTimeout(300);
  await expect(nav.getByRole("link", { name: "Theme" })).toHaveAttribute("aria-current", "location");
});

test("on a short screen the sidebar scrolls inside itself instead of running off the bottom", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 420 });
  await page.goto("/docs");
  const side = await page.locator(".doc-sidebar").evaluate((el) => ({ bottom: el.getBoundingClientRect().bottom, scrolls: el.scrollHeight > el.clientHeight, overflow: getComputedStyle(el).overflowY }));
  expect(side.bottom).toBeLessThanOrEqual(420);
  expect(side.scrolls).toBe(true);
  expect(side.overflow).toBe("auto");
});

// the band starts under the sticky chrome, which is taller on a phone, where the strip sits under the top bar
for (const [from, to, nav] of [[1280, 390, ".doc-strip"], [390, 1280, ".doc-sidebar"]] as const) {
  test(`after the window goes from ${from} to ${to}px wide, a click marks the section it lands on`, async ({ page }) => {
    await page.setViewportSize({ width: from, height: 800 });
    await page.goto("/docs");
    await page.setViewportSize({ width: to, height: 800 });
    const links = page.locator(nav);
    for (const name of ["Theme", "Options", "CDN"]) {
      await links.getByRole("link", { name }).click();
      // the smooth scroll has stopped: two reads 150ms apart agree
      await expect.poll(() => page.evaluate(() => new Promise<number>((r) => {
        const y = scrollY;
        setTimeout(() => r(scrollY - y), 150);
      }))).toBe(0);
      await expect(links.getByRole("link", { name })).toHaveAttribute("aria-current", "location");
    }
  });
}

test.describe("on a 2x screen", () => {
  test.use({ deviceScaleFactor: 2 });

  // Both of the rise's last changes come in steps. Text is drawn on whole device pixels as it moves, so its last pixel of
  // travel is a hop; and Chrome draws no blur under 0.4px, so the blur goes from soft to sharp in one frame. Each reads as
  // a twitch on a block that looks settled, so both happen while the block is still fading in.
  test("the home's blocks come home before their blur clears, and clear it while still fading in", async ({ page }) => {
    await page.goto("/");
    const blocks = page.locator(".hero-rise > *");
    expect(await blocks.count()).toBe(5);
    const late = await blocks.evaluateAll((els) => els.flatMap((el) => {
      const anims = el.getAnimations();
      anims.forEach((a) => a.pause());
      const end = Math.max(...anims.map((a) => Number(a.effect!.getComputedTiming().endTime)));
      for (let t = 0; t <= end; t += 1000 / 120) {
        anims.forEach((a) => (a.currentTime = t));
        const style = getComputedStyle(el);
        const blur = parseFloat(style.filter.match(/blur\(([\d.]+)px\)/)?.[1] ?? "0");
        const away = Math.abs(new DOMMatrixReadOnly(style.transform === "none" ? undefined : style.transform).m42) * devicePixelRatio;
        if (blur < 0.4 && away >= 0.5) return [`${el.className} moves sharp at ${Math.round(t)}ms`];
        if (Number(style.opacity) >= 0.9 && blur >= 0.4) return [`${el.className} is still blurred at ${Math.round(t)}ms`];
      }
      return [];
    }));
    expect(late).toEqual([]);
  });
});

test.describe("without JavaScript", () => {
  test.use({ javaScriptEnabled: false });

  test("the sidebar is plain links that still move the page, and the quick start shows React", async ({ page }) => {
    await page.goto("/docs");
    const nav = page.getByRole("navigation", { name: "Docs" });
    await expect(nav.getByRole("link", { name: "Theme" })).toHaveAttribute("href", "#theme");
    // the script marks the section in view; without it nothing is marked, rather than Install whatever the reader sees
    await expect(page.locator("[aria-current]")).toHaveCount(0);
    await expect(page.locator(".doc-dot")).toHaveCount(0);
    await nav.getByRole("link", { name: "Theme" }).click();
    await expect(page).toHaveURL(/\/docs#theme$/);
    const quick = page.locator("#quick-start");
    await expect(quick.getByRole("tab", { name: "React" })).toHaveAttribute("aria-selected", "true");
    await expect(quick.locator(".code-title")).toHaveText("app/page.tsx");
  });
});

test("a deep link lands on its section at once, without sweeping down the page", async ({ page }) => {
  await page.goto("/docs#theme");
  // read at once, not polled: a smooth scroll from the top would still be under way
  const top = await page.locator("#theme-title").evaluate((el) => el.getBoundingClientRect().top);
  expect(top).toBeGreaterThanOrEqual(54);
  expect(top).toBeLessThan(200);
});

test("back at the top of the page, Install is marked again", async ({ page }) => {
  await page.goto("/docs");
  const nav = page.getByRole("navigation", { name: "Docs" });
  await page.evaluate(() => document.getElementById("theme")!.scrollIntoView({ behavior: "instant" }));
  await expect(nav.getByRole("link", { name: "Theme" })).toHaveAttribute("aria-current", "location");
  // an instant jump, as Back makes under reduced motion: no section passes through the band on the way
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await expect(nav.getByRole("link", { name: "Install" })).toHaveAttribute("aria-current", "location");
});

test("a click in the sidebar still scrolls smoothly to its section", async ({ page }) => {
  await page.goto("/docs");
  await page.getByRole("navigation", { name: "Docs" }).getByRole("link", { name: "Theme" }).click();
  const final = await page.locator("#theme").evaluate((el) => el.getBoundingClientRect().top + scrollY - parseFloat(getComputedStyle(el).scrollMarginTop));
  // just after the click the page is still on its way
  expect(await page.evaluate(() => scrollY)).toBeLessThan(final - 100);
  await expect.poll(() => page.evaluate(() => scrollY)).toBeGreaterThan(final - 2);
});

test("a glide longer than a second keeps the mark on the link picked, every frame of the way", async ({ page }) => {
  await page.goto("/docs");
  const nav = page.locator(".doc-sidebar");
  await nav.getByRole("link", { name: "Install" }).waitFor();
  // every frame from the click's mark on, the marked link, until the page has come to rest
  const watching = page.evaluate(() => new Promise<{ marks: string[]; ms: number }>((done) => {
    const marks = new Set<string>();
    let t0 = 0, last = -1, still = 0;
    const tick = () => {
      const on = document.querySelector(".doc-sidebar a[aria-current]")?.textContent;
      if (on === "Theme" && !t0) t0 = performance.now();
      if (t0 && on) marks.add(on);
      still = scrollY === last ? still + 1 : 0;
      last = scrollY;
      if (still > 30 && scrollY > 0) done({ marks: [...marks], ms: performance.now() - t0 });
      else requestAnimationFrame(tick);
    };
    tick();
  }));
  await nav.getByRole("link", { name: "Theme" }).click();
  const { marks, ms } = await watching;
  // Install to Theme is a long way: the glide outlasts the second a click used to hold the mark for
  expect(ms).toBeGreaterThan(1000);
  expect(marks).toEqual(["Theme"]);
});

test("the top bar's Inspo link opens the story of how Hairline was made, with a clean console", async ({ page }) => {
  const noise = watch(page);
  await page.goto("/");
  await page.getByRole("banner").getByRole("link", { name: "Inspo" }).click();
  await expect(page).toHaveURL(/\/inspo$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("How Hairline was made");
  await expect(page.locator("[data-step]")).toHaveCount(7);
  // the story is the arguing: each pushback names what it changed
  await expect(page.locator("[data-pushback] > li")).toHaveCount(5);
  for (const item of await page.locator("[data-pushback] > li").all()) await expect(item.locator("[data-changed]")).not.toBeEmpty();
  expect(noise).toEqual([]);
});

test("every picture on /inspo loads and says what it shows", async ({ page }) => {
  await page.goto("/inspo");
  const images = page.locator("main img");
  await expect(images).toHaveCount(5);
  for (const img of await images.all()) {
    await img.scrollIntoViewIfNeeded();
    expect((await img.getAttribute("alt"))?.length).toBeGreaterThan(20);
    await expect.poll(() => img.evaluate((el: HTMLImageElement) => el.complete && el.naturalWidth)).toBeGreaterThan(0);
  }
});

test("/inspo fits a phone down to 320px", async ({ page }) => {
  for (const width of [320, 390]) {
    await page.setViewportSize({ width, height: 800 });
    await page.goto("/inspo");
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
  }
});

test("every small label on /inspo is set the same: one face, size, weight and colour", async ({ page }) => {
  await page.goto("/inspo");
  const types = await page.locator(".inspo-label").evaluateAll((els) => els.map((el) => {
    const s = getComputedStyle(el);
    return [s.fontFamily, s.fontSize, s.fontWeight, s.letterSpacing, s.color].join(" ");
  }));
  expect(types.length).toBeGreaterThan(10);
  expect(new Set(types).size).toBe(1);
});

test("the rules on /inspo say they are rules, so their numbers don't read as steps", async ({ page }) => {
  await page.goto("/inspo");
  await expect(page.locator(".inspo-rules .inspo-n")).toHaveText(["Rule 09", "Rule 10"]);
});

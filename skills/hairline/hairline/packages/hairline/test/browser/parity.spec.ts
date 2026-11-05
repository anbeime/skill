import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { play } from "../parity/driver.mjs";
import { FIGURES, INTENSITY, SCRIPTS } from "../parity/scripts.mjs";

/**
 * The package draws what the site draws. Each golden is the site's svg at
 * every checkpoint of a pointer script (test/parity/capture.mjs); the same
 * script is played here against the package, on the same virtual clock.
 */
const file = (p: string) => readFileSync(new URL(p, import.meta.url), "utf8");
const clock = file("../parity/clock.js") + "\nwindow.__freeze(1000);";

/*
 * The goldens hold two things the package no longer draws or says: Riffle's
 * hidden hit bands, and the names the site gives its cards. Both come out of
 * both sides before the comparison, the way ids would; everything else must
 * match character for character.
 */
const strip = (svg: string) => svg.replace(/<g class="bands">.*?<\/g>/, "");
const unname = (id: string, read: string) => (id === "riffle" ? read.replace(/ · .*$/, "") : read);

type Checkpoint = { at: string; read: string; svg: string };

for (const id of FIGURES as string[]) {
  test(`${id} draws what the site draws`, async ({ context, page }) => {
    const golden = JSON.parse(file(`../parity/golden/${id}.json`)) as { checkpoints: Checkpoint[] };
    const intensity = (INTENSITY as Record<string, number>)[id];
    await context.addInitScript(clock);
    await page.goto("/");
    await page.evaluate((id) => { window.__hl.mount(id as "riffle"); }, id);
    const stage = page.locator("#host");
    await stage.locator("svg > *").first().waitFor();
    /* a figure sleeps until its IntersectionObserver reports it on screen, and that report comes on the browser's own time */
    await page.evaluate(() => new Promise((done) => window.__realTimeout(done, 500)));

    const got: Checkpoint[] = await play(page, {
      stage,
      snap: () => page.evaluate(() => ({ svg: document.querySelector("#host > svg")!.innerHTML, read: window.__hl.read() })),
      set: () => page.evaluate((intensity) => window.__hl.figure!.update({ intensity }), intensity),
    }, (SCRIPTS as Record<string, object[]>)[id]);

    expect(got.map((c) => c.at)).toEqual(golden.checkpoints.map((c) => c.at));
    for (const [i, want] of golden.checkpoints.entries()) {
      expect(got[i].read, `caption at "${want.at}"`).toBe(unname(id, want.read));
      expect(strip(got[i].svg), `drawing at "${want.at}"`).toBe(strip(want.svg));
    }
  });
}

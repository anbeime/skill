import { expect, it } from "vitest";
import { beats, moved } from "../../../../skills/hairline-create/look.mjs";

/** moved: the pixels inked in one picture and not the other, over the rest picture's ink. */
it("is nothing when the two pictures are the same", () => {
  expect(moved([1, 1, 0, 0], [1, 1, 0, 0])).toBe(0);
});

it("counts ink that left and ink that arrived", () => {
  expect(moved([1, 1, 0, 0], [1, 0, 1, 0])).toBe(1);
  expect(moved([1, 1, 1, 1], [1, 1, 1, 0])).toBe(0.25);
});

it("is nothing for a rest picture with no ink, not a division by zero", () => {
  expect(moved([0, 0], [0, 1])).toBe(0);
});

it("is nothing when only a stroke's colour changed: the ink is where it was", () => {
  const sameInk = [0, 1, 1, 0];
  expect(moved(sameInk, sameInk.slice())).toBe(0);
});

/** beats: when each frame of the motion strip is taken, in ms after the pointer arrives. */
it("takes the first frame at rest, as the pointer arrives, and the others evenly after it", () => {
  expect(beats(4, 40)).toEqual([0, 40, 80, 120]);
});

it("by default reaches 600ms in sixteen frames, most of the way through the 700ms tween, in four rows of four", () => {
  const b = beats();
  expect(b).toHaveLength(16);
  expect(b.at(-1)).toBe(600);
});

/** launch: the browser order the look uses, shared with read.mjs. A fake Playwright records what it was asked for. */
const fakePw = (chromeWorks: boolean) => {
  const asked: unknown[] = [];
  const chromium = {
    launch: (o?: { channel?: string }) => {
      asked.push(o ?? null);
      return o?.channel && !chromeWorks ? Promise.reject(new Error("no chrome")) : Promise.resolve("browser");
    },
  };
  return { pw: { chromium }, asked };
};

it("launch starts the installed Chrome first, then Playwright's Chromium", async () => {
  const { launch, playwright } = await import("../../../../skills/hairline-create/look.mjs");
  expect(typeof playwright).toBe("function");
  const a = fakePw(true);
  await expect(launch(a.pw)).resolves.toBe("browser");
  expect(a.asked).toEqual([{ channel: "chrome" }]);
  const b = fakePw(false);
  await expect(launch(b.pw)).resolves.toBe("browser");
  expect(b.asked).toEqual([{ channel: "chrome" }, null]);
});

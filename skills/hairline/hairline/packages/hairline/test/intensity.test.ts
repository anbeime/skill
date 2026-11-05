import { describe, expect, it } from "vitest";
import { DEFAULT, TABLE, intensity, parameter, type FigureId } from "../src/intensity";
import { FIGURES, INTENSITY, OPTION } from "./parity/scripts.mjs";

const IDS = Object.keys(TABLE) as FigureId[];

describe("intensity", () => {
  it("keeps a number inside 0…1", () => {
    expect(intensity(0.8)).toBe(0.8);
  });
  it("clamps to 0…1", () => {
    expect(intensity(-3)).toBe(0);
    expect(intensity(7)).toBe(1);
  });
  it("reads a numeric string, as an attribute or a form field would give it", () => {
    expect(intensity("0.8")).toBe(0.8);
    expect(intensity(" 7 ")).toBe(1);
  });
  it.each([undefined, null, NaN, Infinity, -Infinity, "", "  ", "fast", {}, [], true])("falls back to 0.5 for %o", (v) => {
    expect(intensity(v)).toBe(DEFAULT);
    expect(DEFAULT).toBe(0.5);
  });
});

describe("parameter", () => {
  it.each(IDS)("gives %s its table's three values at 0, 0.5 and 1", (id) => {
    expect([0, 0.5, 1].map((i) => parameter(id, i))).toEqual(TABLE[id]);
  });

  it.each(IDS)("moves %s one way only as intensity rises", (id) => {
    const values = Array.from({ length: 21 }, (_, k) => parameter(id, k / 20));
    const falls = id === "slow";
    for (let k = 1; k < values.length; k++) {
      if (falls) expect(values[k]).toBeLessThan(values[k - 1]);
      else expect(values[k]).toBeGreaterThan(values[k - 1]);
    }
  });

  it("rounds to three decimals", () => {
    expect(parameter("riffle", 0.7)).toBe(60);
    expect(parameter("riffle", 0.333)).toBe(26.64);
  });

  it("reads the intensity the way intensity() does", () => {
    expect(parameter("terrain", "0.75")).toBe(4);
    expect(parameter("terrain", 9)).toBe(5);
    expect(parameter("terrain", "fast")).toBe(3);
  });

  /* the parity goldens were captured with raw values; these intensities must land on them exactly. Only the six the site drew have one */
  it.each(FIGURES as Array<keyof typeof OPTION>)("lands %s on the golden's value at its parity intensity", (id) => {
    const raw = OPTION[id][1];
    expect(parameter(id, INTENSITY[id])).toBe(raw);
  });
});

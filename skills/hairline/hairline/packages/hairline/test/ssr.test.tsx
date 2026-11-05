import { createElement } from "react";
import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";

/* No DOM here on purpose: this is what a server sees. */
describe("on the server", () => {
  it("imports both entries without touching a DOM", async () => {
    expect(typeof document).toBe("undefined");
    expect(typeof window).toBe("undefined");
    await expect(import("../src/index")).resolves.toBeTypeOf("object");
    await expect(import("../src/react")).resolves.toBeTypeOf("object");
  });

  it("renders a component as an empty box of the right shape", async () => {
    const { Riffle } = await import("../src/react");
    const html = renderToString(createElement(Riffle, { className: "w-80", intensity: 0.8, theme: "dark", label: "Cards", play: true, onRead() {} }));
    expect(html).toBe('<div class="w-80" style="aspect-ratio:5 / 4"></div>');
  });

  it("says what is wrong when a figure is mounted without a DOM", async () => {
    const { riffle } = await import("../src/index");
    expect(() => riffle({} as HTMLElement)).toThrow(/needs a DOM/);
  });
});

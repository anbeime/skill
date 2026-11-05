import { existsSync, readdirSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { PAGES } from "@/lib/share";

const APP = new URL("../app/", import.meta.url);

describe("the sitemap's pages", () => {
  it("are every page in app/ but the card's own, which is a picture to photograph and not a page to read", () => {
    const routes = readdirSync(APP, { withFileTypes: true })
      .filter((entry) => entry.isDirectory() && existsSync(new URL(`${entry.name}/page.tsx`, APP)))
      .map((entry) => `/${entry.name}`);
    expect([...PAGES].sort()).toEqual(["/", ...routes.filter((route) => route !== "/og")].sort());
  });
});

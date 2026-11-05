import { defineConfig, type Options } from "tsup";

const shared = { format: ["esm"], target: "es2020", dts: true, sourcemap: true } satisfies Options;

/**
 * The React entry imports the figures from "./index" in source, so types and
 * tests need no build. In the bundle that import becomes the package's own
 * name and stays external: both entries then run on one copy of the core, and
 * so on one frame loop.
 */
const self: NonNullable<Options["esbuildPlugins"]>[number] = {
  name: "core-by-package-name",
  setup(build) {
    build.onResolve({ filter: /^\.\/index$/ }, () => ({ path: "@lucasmarkes/hairline", external: true }));
  },
};

export default defineConfig([
  { ...shared, entry: ["src/index.ts"] },
  { ...shared, entry: ["src/react.tsx"], external: ["react"], esbuildPlugins: [self], banner: { js: '"use client";' } },
]);

/**
 * The browser tests' server: the harness page and the package source, bundled
 * by esbuild at start, and the skill's bench with its examples on it, built at
 * start too. Playwright starts it (playwright.config.ts).
 */
import { build } from "esbuild";
import { readFileSync } from "node:fs";
import { createServer } from "node:http";
import { fileURLToPath } from "node:url";
import { assemble } from "../../../../skills/hairline-create/build.mjs";

const PORT = 4310;
const here = (p) => fileURLToPath(new URL(p, import.meta.url));

const bundle = await build({ entryPoints: [here("./entry.ts")], bundle: true, format: "esm", target: "es2020", write: false });
/* The skill's bench (skills/hairline-create), with a figure on it: what its agent hands over. */
const example = (name) => assemble(readFileSync(here(`../../../../skills/hairline-create/examples/${name}.js`), "utf8"));
const THROWS = `hairline({ name: "throws", means: "A figure that fails at mount.", rules: [5], range: [0, 1, 2], mount() { throw new Error("no drawing today"); } });`;
const routes = {
  "/": ["text/html", readFileSync(here("./harness.html"))],
  "/entry.js": ["text/javascript", bundle.outputFiles[0].contents],
  "/bench/terrain": ["text/html", example("terrain")],
  "/bench/riffle": ["text/html", example("riffle")],
  "/bench/throws": ["text/html", assemble(THROWS)],
};

createServer((req, res) => {
  const hit = routes[new URL(req.url, "http://x").pathname];
  if (!hit) { res.writeHead(404).end(); return; }
  res.writeHead(200, { "content-type": `${hit[0]}; charset=utf-8`, "cache-control": "no-store" }).end(hit[1]);
}).listen(PORT, () => console.log(`harness on http://localhost:${PORT}`));
